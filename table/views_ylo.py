from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, Course, YLOPerPLOSemester
from django.contrib import messages

# Convert semester index (1..8) to "Year/Term" like "1/1", "1/2", ..., "4/2"
def convert_semester(sem: int) -> str:
    year = (sem - 1) // 2 + 1
    term = 1 if sem % 2 == 1 else 2
    return f"{year}/{term}"

# YLO Study Plan page
def ylo_study_plan(request, curriculum_id, semester):
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # Courses in this semester
    courses = Course.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester
    ).order_by('course_code')

    # YLO summaries in this semester
    ylo_entries = YLOPerPLOSemester.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester
    ).order_by('plo')

    # Build ylo_list with non-empty summaries
    ylo_list = []
    semester_str = convert_semester(semester)
    for idx, ylo in enumerate(ylo_entries, start=1):
        if ylo.summary_text and str(ylo.summary_text).strip():
            ylo_code = f"YLO {semester_str}-{idx}"
            ylo_list.append({
                'code': ylo_code,
                'summary_text': ylo.summary_text,
            })

    return render(request, 'table/ylo_study_plan.html', {
        'curriculum_id': curriculum_id,
        'semester': semester,
        'semester_str': semester_str,
        'courses': courses,
        'ylo_list': ylo_list,
        'access_mode': mode,  # used by the template to toggle read-only/edit
    })

# Save K/S/E/C values into Course
def save_ylo_studyplan(request, curriculum_id, semester):
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    if request.method == 'POST' and mode == 'edit':
        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)
        courses = Course.objects.using(db).filter(curriculum=curriculum, semester=semester)

        for course in courses:
            course.knowledge = (request.POST.get(f'k_{course.id}', '')).strip()
            course.skills    = (request.POST.get(f's_{course.id}', '')).strip()
            course.ethics    = (request.POST.get(f'e_{course.id}', '')).strip()
            course.character = (request.POST.get(f'c_{course.id}', '')).strip()
            course.save(using=db)

        # update_ylo_for_curriculum(curriculum)  # call if you want auto-prune after save
        messages.success(request, "✅ YLO Study Plan saved successfully.")

    return redirect('ylo_study_plan', curriculum_id=curriculum_id, semester=semester)

def update_ylo_for_curriculum(curriculum):
    """
    Ensure YLO records exist only for PLOs that actually have credits
    in each semester; delete YLOs whose PLO has no credited courses.
    """
    from .models import Course, YLOPerPLOSemester

    for sem in range(1, 9):
        plo_with_credits = set()
        courses = Course.objects.using('real').filter(curriculum=curriculum, semester=sem)

        for course in courses:
            if not course.plo:
                continue
            plo_tag = course.plo.split(':')[0].strip()
            if plo_tag and course.credits and course.credits > 0:
                plo_with_credits.add(plo_tag)

        # Delete YLOs for PLOs that have no credited courses in this semester
        for ylo in YLOPerPLOSemester.objects.using('real').filter(curriculum=curriculum, semester=sem):
            ylo_plo_tag = ylo.plo.strip().split(":")[0].strip() if ylo.plo else ''
            if ylo_plo_tag not in plo_with_credits:
                ylo.delete()
            else:
                # keep
                pass
