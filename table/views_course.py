from django.shortcuts import render, redirect, get_object_or_404
from .models import CreditRow, Course, Curriculum
from django.contrib import messages

def course_list(request, curriculum_id, row_id, semester):
    # access mode
    mode = request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'
    readonly = (mode != 'edit')

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # PLO choices & descriptions (labels that start with "PLO")
    plo_rows = CreditRow.objects.using(db).filter(curriculum=curriculum, row_type='plo')
    plo_choices = []
    plo_descriptions = {}
    for r in plo_rows:
        if r.name:
            parts = r.name.split()
            if parts[0].startswith("PLO"):
                label = parts[0]
                desc = " ".join(parts[1:]) if len(parts) > 1 else ""
                if label not in plo_choices:
                    plo_choices.append(label)
                    plo_descriptions[label] = desc

    # Free Electives
    if row_id == 'free_elective':
        courses = Course.objects.using(db).filter(
            curriculum=curriculum,
            category='free_elective',
            semester=semester
        ).order_by('course_code')
        return render(request, 'table/course_list.html', {
            'curriculum_id': curriculum_id,
            'row': {'id': 'free_elective', 'name': 'Free Electives'},
            'semester': semester,
            'courses': courses,
            'plo_choices': plo_choices,
            'plo_descriptions': plo_descriptions,
            'readonly': readonly,
        })

    # Regular rows
    row = get_object_or_404(CreditRow.objects.using(db), curriculum=curriculum, id=row_id)
    courses = Course.objects.using(db).filter(
        curriculum=curriculum,
        credit_row=row,
        semester=semester
    ).order_by('course_code')

    return render(request, 'table/course_list.html', {
        'curriculum_id': curriculum_id,
        'row': row,
        'semester': semester,
        'courses': courses,
        'plo_choices': plo_choices,
        'plo_descriptions': plo_descriptions,
        'readonly': readonly,
    })


def save_course_list(request, curriculum_id, row_id, semester):
    mode = request.session.get('access_mode', 'view')
    if mode != 'edit':
        messages.error(request, "🚫 Cannot save in view-only mode.")
        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)

    db = 'real'

    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

        codes = request.POST.getlist('course_code[]')
        names = request.POST.getlist('course_name[]')
        credits = request.POST.getlist('credits[]')
        plos = request.POST.getlist('plo[]')

        if not any((code or '').strip() for code in codes):
            messages.warning(request, "⚠️ No course code provided.")
            return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)

        if row_id == 'free_elective':
            existing_courses = Course.objects.using(db).filter(
                curriculum=curriculum,
                category='free_elective',
                semester=semester
            )
            existing_map = {c.course_code.strip(): c for c in existing_courses}
            updated_codes = set()

            for code, name, credit, plo in zip(codes, names, credits, plos):
                code_key = (code or '').strip()
                if not code_key:
                    continue
                updated_codes.add(code_key)
                if code_key in existing_map:
                    course = existing_map[code_key]
                    course.course_name = (name or '').strip()
                    course.credits = int(credit or 0)
                    course.plo = (plo or '').strip()
                    course.save(using=db)
                else:
                    Course.objects.using(db).create(
                        curriculum=curriculum,
                        category='free_elective',
                        semester=semester,
                        course_code=code_key,
                        course_name=(name or '').strip(),
                        credits=int(credit or 0),
                        plo=(plo or '').strip()
                    )

            # delete removed
            for code_key, course in existing_map.items():
                if code_key not in updated_codes:
                    course.delete(using=db)

            messages.success(request, "✅ Saved Free Electives successfully.")
            return redirect('course_list', curriculum_id=curriculum_id, row_id='free_elective', semester=semester)

        # Regular row
        row = get_object_or_404(CreditRow.objects.using(db), curriculum=curriculum, id=row_id)

        existing_courses = Course.objects.using(db).filter(
            curriculum=curriculum,
            credit_row=row,
            semester=semester
        )
        existing_map = {c.course_code.strip(): c for c in existing_courses}
        updated_codes = set()

        for code, name, credit, plo in zip(codes, names, credits, plos):
            code_key = (code or '').strip()
            if not code_key:
                continue
            updated_codes.add(code_key)
            if code_key in existing_map:
                course = existing_map[code_key]
                course.course_name = (name or '').strip()
                course.credits = int(credit or 0)
                course.plo = (plo or '').strip()
                course.save(using=db)
            else:
                Course.objects.using(db).create(
                    curriculum=curriculum,
                    credit_row=row,
                    semester=semester,
                    course_code=code_key,
                    course_name=(name or '').strip(),
                    credits=int(credit or 0),
                    plo=(plo or '').strip()
                )

        # delete removed
        for code_key, course in existing_map.items():
            if code_key not in updated_codes:
                course.delete(using=db)

        # If user edited the PLO row name (rare for this page), accept it
        plo_name_key = f'plo_name_{row_id}'
        if plo_name_key in request.POST:
            row.name = request.POST[plo_name_key].strip()
            row.save(using=db)

        messages.success(request, "✅ Saved this category’s course list.")
        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)


def reset_course_list(request, curriculum_id, row_id, semester):
    mode = request.session.get('access_mode', 'view')
    if mode != 'edit':
        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)

    db = 'real'

    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

        if row_id == 'free_elective':
            Course.objects.using(db).filter(
                curriculum=curriculum,
                category='free_elective',
                semester=semester
            ).delete()
            return redirect('course_list', curriculum_id=curriculum_id, row_id='free_elective', semester=semester)

        row = get_object_or_404(CreditRow.objects.using(db), curriculum=curriculum, id=row_id)
        Course.objects.using(db).filter(
            curriculum=curriculum,
            credit_row=row,
            semester=semester
        ).delete()

        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)
