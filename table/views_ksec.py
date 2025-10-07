from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, KSECItem
from django.db import transaction

TYPE_MAP = {
    'K': 'Knowledge',
    'S': 'Skills',
    'E': 'Ethics',
    'C': 'Character',
}

def ksec_edit(request, curriculum_id, semester, type):
    # Validate type
    if type not in TYPE_MAP:
        return redirect('curriculum_select')

    type_name = TYPE_MAP[type]

    # Respect access mode and choose the database
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    # Load items (not semester-specific), ordered by sort_order then id
    items = KSECItem.objects.using(db).filter(
        curriculum=curriculum,
        type=type
    ).order_by('sort_order', 'id')

    # Save only in edit mode
    if request.method == 'POST' and mode == 'edit':
        with transaction.atomic(using=db):
            total = int(request.POST.get('total_items', 0))
            keep_ids = set()
            new_items = []

            # Scan enough indices to cover added rows
            for i in range(total + 50):
                item_id = request.POST.get(f'item_id_{i}')
                desc = request.POST.get(f'item_{i}')
                category_type = request.POST.get(f'item_type_{i}')

                if desc and category_type in ['GE', 'CE']:
                    desc = desc.strip()
                    if item_id and item_id.isdigit():
                        obj = KSECItem.objects.using(db).filter(
                            id=int(item_id),
                            curriculum=curriculum
                        ).first()
                        if obj:
                            obj.description = desc
                            obj.category_type = category_type
                            obj.sort_order = i  # keep the visual order
                            obj.save(using=db)
                            keep_ids.add(obj.id)
                    else:
                        new_items.append(KSECItem(
                            curriculum=curriculum,
                            semester=0,           # same across semesters
                            type=type,
                            category_type=category_type,
                            description=desc,
                            sort_order=i
                        ))

            if new_items:
                created = KSECItem.objects.using(db).bulk_create(new_items)
                keep_ids.update(obj.id for obj in created)

            # Remove items that were deleted in the form
            KSECItem.objects.using(db).filter(
                curriculum=curriculum,
                type=type
            ).exclude(id__in=keep_ids).delete()

        return redirect('ksec_edit', curriculum_id=curriculum_id, semester=semester, type=type)

    # Build "Year/Term" label, e.g. "1/1", "1/2", ..., "4/2"
    year = (semester - 1) // 2 + 1
    term = 1 if semester % 2 == 1 else 2
    semester_str = f"{year}/{term}"

    return render(request, 'table/ksec_edit.html', {
        'curriculum': curriculum,
        'semester': semester,
        'semester_str': semester_str,
        'type': type,              # 'K', 'S', 'E', or 'C'
        'type_name': type_name,    # 'Knowledge', 'Skills', 'Ethics', 'Character'
        'items': items,
        'access_mode': mode,       # controls read-only vs edit in the template
    })
