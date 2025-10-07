from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import CreditRow, Course, YLOPerPLOSemester
from django.contrib import messages

def convert_semester(sem: int) -> str:
    """Return 'Year/Term' like '1/1', '1/2', ... '4/2'."""
    year = (sem - 1) // 2 + 1
    term = 1 if sem % 2 == 1 else 2
    return f"{year}/{term}"

def plo_course_list(request, curriculum_id, row_id, semester):
    # respect explicit ?mode= or fallback to session
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    # current PLO row
    plo_row = get_object_or_404(CreditRow.objects.using(db), id=row_id, curriculum_id=curriculum_id)
    plo_label = plo_row.name.split()[0] if plo_row.name else ''

    # courses that match this PLO in the selected semester
    matching_courses = Course.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester,
        plo=plo_label,
    ).order_by('course_code')

    total_credits = sum(course.credits for course in matching_courses)

    # total credits for this PLO across all semesters
    total_credits_all = Course.objects.using(db).filter(
        curriculum_id=curriculum_id,
        plo=plo_label
    ).aggregate(Sum('credits'))['credits__sum'] or 0

    percent_of_total = round((total_credits / total_credits_all) * 100, 2) if total_credits_all else 0

    semester_str = convert_semester(semester)

    # Determine YLO index for this semester (only rows with non-zero credits count)
    all_plo_rows = CreditRow.objects.using(db).filter(
        curriculum_id=curriculum_id,
        row_type='plo'
    ).order_by('id')

    non_zero_rows = []
    for row in all_plo_rows:
        label = row.name.split()[0] if row.name else ''
        credits = Course.objects.using(db).filter(
            curriculum_id=curriculum_id,
            semester=semester,
            plo=label,
        ).aggregate(Sum('credits'))['credits__sum'] or 0
        if credits > 0:
            non_zero_rows.append(row)

    try:
        ylo_number = non_zero_rows.index(plo_row) + 1
    except ValueError:
        ylo_number = 1

    ylo_summary = YLOPerPLOSemester.objects.using(db).filter(
        curriculum_id=curriculum_id,
        plo=plo_label,
        semester=semester
    ).first()

    return render(request, 'table/plo_course_list.html', {
        'row': plo_row,
        'semester': semester,
        'semester_str': semester_str,
        'courses': matching_courses,
        'total_credits': total_credits,
        'percent_of_total': percent_of_total,
        'access_mode': mode,   # 'edit' or 'view' for the template conditionals
        'ylo_summary': ylo_summary,
        'ylo_number': ylo_number,
    })

def save_plo_course_list(request, curriculum_id, row_id, semester):
    if request.method == 'POST':
        summary_text = (request.POST.get('summary_text') or '').strip()
        plo_name = get_object_or_404(CreditRow.objects.using('real'), id=row_id).name
        plo_label = plo_name.split()[0] if plo_name else ''

        YLOPerPLOSemester.objects.using('real').update_or_create(
            curriculum_id=curriculum_id,
            plo=plo_label,
            semester=semester,
            defaults={'summary_text': summary_text}
        )
        messages.success(request, "✅ YLO saved successfully.")
    return redirect('plo_course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)
