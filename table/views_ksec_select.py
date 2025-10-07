from django.shortcuts import render, get_object_or_404
from .models import Curriculum, KSECItem

TYPE_MAP = {
    'K': 'Knowledge',
    'S': 'Skills',
    'E': 'Ethics',
    'C': 'Character',
}

def ksec_item_select(request, curriculum_id):
    semester = request.GET.get('semester')
    ksec_type = request.GET.get('type')
    course_id = request.GET.get('course_id')

    # Validate required parameters
    if not semester or not ksec_type:
        return render(request, 'table/error.html', {
            'message': 'Please specify both the semester and the K/S/E/C type.'
        })

    # Respect access mode and choose database
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # Load items (semester-agnostic) and generate codes
    raw_items = list(KSECItem.objects.using(db).filter(
        curriculum=curriculum,
        semester=0,        # shared across semesters
        type=ksec_type
    ).order_by('sort_order', 'id'))

    for idx, item in enumerate(raw_items):
        # e.g., GE(K)1, CE(S)2, ...
        item.code = f"{item.category_type}({ksec_type}){idx + 1}"

    # Build "Year X / Term Y"
    sem = int(semester)
    year = (sem - 1) // 2 + 1
    term = 1 if sem % 2 == 1 else 2
    semester_str = f"Year {year} / Term {term}"

    return render(request, 'table/ksec_item_select.html', {
        'curriculum': curriculum,
        'semester': semester,
        'semester_str': semester_str,
        'type': ksec_type,                            # 'K', 'S', 'E', or 'C'
        'type_name': TYPE_MAP.get(ksec_type, ksec_type),
        'course_id': course_id,
        'items': raw_items,
        'access_mode': mode,                          # 'view' or 'edit'
    })
