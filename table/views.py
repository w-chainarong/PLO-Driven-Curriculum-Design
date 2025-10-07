from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import CreditRow, Course
import re
from django.contrib import messages
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
import zipfile
import os
import io
from .models import Curriculum, CreditRow, Course, YLOPerPLOSemester, KSECItem
from .models import CLO, CLOSummary
from django.http import HttpResponse
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# ---------- UI headers (English) ----------
headers = [
    'Year 1/1', 'Year 1/2', 'Year 2/1', 'Year 2/2',
    'Year 3/1', 'Year 3/2', 'Year 4/1', 'Year 4/2'
]

from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum

def curriculum_select(request):
    if request.method == 'POST':
        curriculum_id = request.POST.get('curriculum')
        mode = request.POST.get('mode')
        password = request.POST.get('password', '').strip()

        if not curriculum_id:
            return render(request, 'table/curriculum_select.html', {
                'curriculums': Curriculum.objects.using('default').all(),
                'error_message': 'Please select a curriculum.',
            })

        curriculum = get_object_or_404(Curriculum.objects.using('default'), pk=curriculum_id)

        if mode == 'edit' and password != curriculum.password:
            return render(request, 'table/curriculum_select.html', {
                'curriculums': Curriculum.objects.using('default').all(),
                'error_message': 'Incorrect password.',
            })

        request.session['access_mode'] = mode  # save mode in session
        return redirect('credit_table', curriculum_id=curriculum.id)

    return render(request, 'table/curriculum_select.html', {
        'curriculums': Curriculum.objects.using('default').all()
    })


def credit_table(request, curriculum_id):
    mode = request.session.get('access_mode', 'view')  # 'view' or 'edit'
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    if request.method == 'POST' and mode == 'edit':
        new_name = request.POST.get('curriculum_name', '').strip()
        if new_name and new_name != curriculum.name:
            curriculum.name = new_name
            curriculum.save(using='real')  # always save into real DB

        def delete_removed_rows(row_type, id_prefixes):
            posted_ids = set()
            for prefix in id_prefixes:
                pattern = re.compile(rf'{prefix}_(\d+)')
                for key in request.POST:
                    match = pattern.match(key)
                    if match:
                        try:
                            val = request.POST.get(key)
                            if val:
                                posted_ids.add(int(val))
                        except (TypeError, ValueError):
                            continue
            if posted_ids:
                CreditRow.objects.using('real').filter(
                    curriculum=curriculum,
                    row_type=row_type
                ).exclude(id__in=posted_ids).delete()

        def save_rows(row_type, prefix, credit_prefix):
            pattern = re.compile(rf'{prefix}_(\d+)')
            indices = sorted({match.group(1) for key in request.POST for match in [pattern.match(key)] if match})

            for index in indices:
                name = request.POST.get(f'{prefix}_{index}', '').strip()
                if not name:
                    continue

                credits = [int(request.POST.get(f'{credit_prefix}_{index}_{j}', 0)) for j in range(8)]
                row_id_key = f'{row_type}_id_{index}'
                row_id = request.POST.get(row_id_key)

                if row_id:
                    try:
                        row = CreditRow.objects.using('real').get(pk=row_id, curriculum=curriculum, row_type=row_type)
                        row.name = name
                        for i in range(8):
                            setattr(row, f'credits_sem{i+1}', credits[i])
                        row.save(using='real')
                    except CreditRow.DoesNotExist:
                        continue
                else:
                    CreditRow.objects.using('real').create(
                        curriculum=curriculum,
                        name=name,
                        row_type=row_type,
                        **{f'credits_sem{i+1}': credits[i] for i in range(8)}
                    )

        # delete rows not present in POST
        delete_removed_rows('plo', ['plo_id'])
        delete_removed_rows('core', ['core_id'])
        delete_removed_rows('general', ['general_id'])

        # update existing + create new rows
        save_rows('general', 'general_name', 'general_credit')
        save_rows('core', 'core_name', 'core_credit')
        save_rows('plo', 'plo_name', 'plo_credit')
        save_rows('general', 'general_name_new', 'general_credit_new')
        save_rows('core', 'core_name_new', 'core_credit_new')
        save_rows('plo', 'plo_name_new', 'plo_credit_new')

        # sync YLO with PLO/Course
        from .views_ylo import update_ylo_for_curriculum
        update_ylo_for_curriculum(curriculum)
        sync_plo_credits_to_creditrow(curriculum)

        # Free Electives row name (English)
        free_name = 'Free Electives'
        free_credits = [int(request.POST.get(f'{free_name}_{i}', 0)) for i in range(8)]
        CreditRow.objects.using('real').update_or_create(
            curriculum=curriculum,
            name=free_name,
            row_type='free',
            defaults={f'credits_sem{i+1}': free_credits[i] for i in range(8)}
        )

        return redirect('credit_table', curriculum_id=curriculum.id)

    all_rows = CreditRow.objects.using(db).filter(curriculum=curriculum)

    general_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='general')]
    core_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='core')]
    plo_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='plo').order_by('id')]
    free_elective = all_rows.filter(row_type='free').first()
    free_elective_tuple = (free_elective.name, free_elective.credit_list(), free_elective.total_credits()) if free_elective else None
    has_saved = request.method == 'POST'

    # compute totals per (PLO row, semester) based on courses
    plo_course_totals = {}
    for row in all_rows.filter(row_type='plo'):
        if row.name:
            plo_tag = row.name.split()[0]  # e.g., "PLO1:" or "PLO1"
            for semester in range(1, 9):
                general_core_sum = Course.objects.using(db).filter(
                    curriculum=curriculum,
                    semester=semester,
                    plo=plo_tag,
                    credit_row__row_type__in=['general', 'core']
                ).aggregate(Sum('credits'))['credits__sum'] or 0
                free_sum = Course.objects.using(db).filter(
                    curriculum=curriculum,
                    semester=semester,
                    plo=plo_tag,
                    category='free_elective'
                ).aggregate(Sum('credits'))['credits__sum'] or 0
                key = f"{row.id}_{semester}"
                plo_course_totals[key] = general_core_sum + free_sum

    # semester totals for all PLOs
    plo_semester_totals = {i: 0 for i in range(1, 9)}
    for key, value in plo_course_totals.items():
        _, semester = key.split('_')
        plo_semester_totals[int(semester)] += value

    total_credits_all = sum(row.total_credits() for row in all_rows)
    plo_percentages = {
        str(row.id): round((row.total_credits() / total_credits_all) * 100, 2) if total_credits_all else 0
        for row in all_rows.filter(row_type='plo')
    }

    return render(request, 'table/credit_table.html', {
        'curriculum': curriculum,
        'headers': headers,
        'general_rows': general_rows,
        'core_rows': core_rows,
        'plo_rows': plo_rows,
        'free_elective': free_elective_tuple,
        'has_saved': has_saved,
        'plo_course_totals': plo_course_totals,
        'plo_semester_totals': plo_semester_totals,
        'plo_percentages': plo_percentages,
        'access_mode': mode,
    })


def reset_credit_table(request, curriculum_id):
    mode = request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    if mode != 'edit':
        return redirect('credit_table', curriculum_id=curriculum_id)

    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    if request.method == 'POST':
        # delete CLO & CLOSummary linked to Course
        CLO.objects.using(db).filter(course__curriculum=curriculum).delete()
        CLOSummary.objects.using(db).filter(course__curriculum=curriculum).delete()
        # delete Course
        Course.objects.using(db).filter(curriculum=curriculum).delete()
        # delete YLO summary
        YLOPerPLOSemester.objects.using(db).filter(curriculum=curriculum).delete()
        # delete KSEC items
        KSECItem.objects.using(db).filter(curriculum=curriculum).delete()
        # delete CreditRows
        CreditRow.objects.using(db).filter(curriculum=curriculum).delete()
        # do not delete Curriculum itself
        return redirect('credit_table', curriculum_id=curriculum.id)

    # (unreached Thai-render block removed for clarity)

    # In edit mode: create fresh defaults (English)
    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    if request.method == 'POST':
        CreditRow.objects.using(db).filter(
            curriculum=curriculum,
            row_type__in=['general', 'core', 'plo', 'free']
        ).delete()

        general_data = [
            ('Language', [0]*8),
            ('Social Sciences', [0]*8),
            ('Humanities', [0]*8),
            ('Physical Education & Recreation', [0]*8),
            ('Science', [0]*8),
            ('Mathematics & Computer', [0]*8),
            ('Integration', [0]*8)
        ]
        core_data = [
            ('Basic Science & Mathematics', [0]*8),
            ('Basic Engineering', [0]*8),
            ('Compulsory Professional Courses', [0]*8),
            ('Elective Professional Courses', [0]*8),
            ('Professional Experience Enhancement', [0]*8)
        ]
        plo_data = [('PLO1:', [0]*8)]

        def create_rows(row_type, data):
            for name, credits in data:
                CreditRow.objects.using(db).create(
                    curriculum=curriculum,
                    name=name,
                    row_type=row_type,
                    **{f'credits_sem{i+1}': credits[i] for i in range(8)}
                )

        create_rows('general', general_data)
        create_rows('core', core_data)
        create_rows('plo', plo_data)

        CreditRow.objects.using(db).create(
            curriculum=curriculum,
            name='Free Electives',
            row_type='free',
            **{f'credits_sem{i+1}': 0 for i in range(8)}
        )

        return redirect('credit_table', curriculum_id=curriculum.id)
    
def sync_curriculum_real_to_example(request, curriculum_id):
    if request.session.get('access_mode') != 'edit':
        messages.error(request, "🚫 You must be in Edit mode to back up data.")
        return redirect('credit_table', curriculum_id=curriculum_id)

    curriculum_real = Curriculum.objects.using('real').filter(id=curriculum_id).first()
    if not curriculum_real:
        messages.error(request, f"❌ Curriculum ID={curriculum_id} not found in the 'real' database.")
        return redirect('credit_table', curriculum_id=curriculum_id)

    # wipe children in example
    CreditRow.objects.using('default').filter(curriculum_id=curriculum_id).delete()
    Course.objects.using('default').filter(curriculum_id=curriculum_id).delete()
    YLOPerPLOSemester.objects.using('default').filter(curriculum_id=curriculum_id).delete()
    KSECItem.objects.using('default').filter(curriculum_id=curriculum_id).delete()
    CLO.objects.using('default').filter(course__curriculum_id=curriculum_id).delete()
    CLOSummary.objects.using('default').filter(course__curriculum_id=curriculum_id).delete()

    # copy/update Curriculum (no delete)
    Curriculum.objects.using('default').update_or_create(
        id=curriculum_real.id,
        defaults={
            'name': curriculum_real.name,
            'password': curriculum_real.password,
            'clo_edit_password': curriculum_real.clo_edit_password
        }
    )

    # copy CreditRow
    real_to_default_creditrow = {}
    for row in CreditRow.objects.using('real').filter(curriculum_id=curriculum_id):
        new_row = CreditRow.objects.using('default').create(
            curriculum_id=row.curriculum_id,
            name=row.name,
            row_type=row.row_type,
            credits_sem1=row.credits_sem1,
            credits_sem2=row.credits_sem2,
            credits_sem3=row.credits_sem3,
            credits_sem4=row.credits_sem4,
            credits_sem5=row.credits_sem5,
            credits_sem6=row.credits_sem6,
            credits_sem7=row.credits_sem7,
            credits_sem8=row.credits_sem8
        )
        real_to_default_creditrow[row.id] = new_row

    # copy Course with same IDs
    real_to_default_course = {}
    for course in Course.objects.using('real').filter(curriculum_id=curriculum_id):
        new_credit_row = real_to_default_creditrow.get(course.credit_row.id) if course.credit_row else None

        new_course = Course(
            id=course.id,
            curriculum_id=course.curriculum_id,
            course_code=course.course_code,
            course_name=course.course_name,
            credits=course.credits,
            semester=course.semester,
            plo=course.plo,
            category=course.category,
            credit_row=new_credit_row,
            knowledge=course.knowledge,
            skills=course.skills,
            ethics=course.ethics,
            character=course.character,
            description=course.description
        )
        new_course.save(using='default', force_insert=True)
        real_to_default_course[course.id] = new_course

    # copy YLOPerPLOSemester
    for ylo in YLOPerPLOSemester.objects.using('real').filter(curriculum_id=curriculum_id):
        YLOPerPLOSemester.objects.using('default').create(
            curriculum_id=ylo.curriculum_id,
            plo=ylo.plo,
            semester=ylo.semester,
            summary_text=ylo.summary_text
        )

    # copy KSECItem
    for item in KSECItem.objects.using('real').filter(curriculum_id=curriculum_id):
        KSECItem.objects.using('default').create(
            curriculum_id=item.curriculum_id,
            semester=0,
            type=item.type,
            category_type=item.category_type,
            description=item.description,
            sort_order=item.sort_order
        )

    # copy CLO & CLOSummary
    for course in Course.objects.using('real').filter(curriculum_id=curriculum_id):
        new_course = real_to_default_course.get(course.id)
        if not new_course:
            continue

        for clo in CLO.objects.using('real').filter(course=course):
            CLO.objects.using('default').create(
                course=new_course,
                index=clo.index,
                clo=clo.clo,
                bloom=clo.bloom,
                k=clo.k,
                s=clo.s,
                e=clo.e,
                c=clo.c
            )

        summary = CLOSummary.objects.using('real').filter(course=course).first()
        if summary:
            CLOSummary.objects.using('default').create(
                course=new_course,
                bloom_score=summary.bloom_score,
                k_percent=summary.k_percent,
                s_percent=summary.s_percent,
                e_percent=summary.e_percent,
                c_percent=summary.c_percent
            )

    messages.success(request, "✅ Curriculum backed up to the example database.")
    return redirect('credit_table', curriculum_id=curriculum_id)


def sync_curriculum_example_to_real(request, curriculum_id):
    if request.session.get('access_mode') != 'edit':
        messages.error(request, "🚫 You must be in Edit mode to restore data.")
        return redirect('credit_table', curriculum_id=curriculum_id)

    curriculum_example = get_object_or_404(Curriculum.objects.using('default'), id=curriculum_id)

    # wipe old in real
    CLO.objects.using('real').filter(course__curriculum_id=curriculum_id).delete()
    CLOSummary.objects.using('real').filter(course__curriculum_id=curriculum_id).delete()
    CreditRow.objects.using('real').filter(curriculum_id=curriculum_id).delete()
    Course.objects.using('real').filter(curriculum_id=curriculum_id).delete()
    YLOPerPLOSemester.objects.using('real').filter(curriculum_id=curriculum_id).delete()
    KSECItem.objects.using('real').filter(curriculum_id=curriculum_id).delete()
    Curriculum.objects.using('real').filter(id=curriculum_id).delete()

    # copy Curriculum
    Curriculum.objects.using('real').create(
        id=curriculum_example.id,
        name=curriculum_example.name,
        password=curriculum_example.password,
        clo_edit_password=curriculum_example.clo_edit_password
    )

    # copy CreditRow (same IDs)
    example_to_real_creditrow = {}
    for row in CreditRow.objects.using('default').filter(curriculum_id=curriculum_id):
        new_row = CreditRow.objects.using('real').create(
            id=row.id,
            curriculum_id=row.curriculum_id,
            name=row.name,
            row_type=row.row_type,
            credits_sem1=row.credits_sem1,
            credits_sem2=row.credits_sem2,
            credits_sem3=row.credits_sem3,
            credits_sem4=row.credits_sem4,
            credits_sem5=row.credits_sem5,
            credits_sem6=row.credits_sem6,
            credits_sem7=row.credits_sem7,
            credits_sem8=row.credits_sem8
        )
        example_to_real_creditrow[row.id] = new_row

    # copy Course (same IDs)
    example_to_real_course = {}
    for course in Course.objects.using('default').filter(curriculum_id=curriculum_id):
        new_credit_row = example_to_real_creditrow.get(course.credit_row.id) if course.credit_row else None

        new_course = Course(
            id=course.id,
            curriculum_id=course.curriculum_id,
            course_code=course.course_code,
            course_name=course.course_name,
            credits=course.credits,
            semester=course.semester,
            plo=course.plo,
            category=course.category,
            credit_row=new_credit_row,
            knowledge=course.knowledge,
            skills=course.skills,
            ethics=course.ethics,
            character=course.character,
            description=course.description
        )
        new_course.save(using='real', force_insert=True)
        example_to_real_course[course.id] = new_course

    # copy YLOPerPLOSemester
    for ylo in YLOPerPLOSemester.objects.using('default').filter(curriculum_id=curriculum_id):
        YLOPerPLOSemester.objects.using('real').create(
            curriculum_id=ylo.curriculum_id,
            plo=ylo.plo,
            semester=ylo.semester,
            summary_text=ylo.summary_text
        )

    # copy KSECItem
    for item in KSECItem.objects.using('default').filter(curriculum_id=curriculum_id):
        KSECItem.objects.using('real').create(
            curriculum_id=item.curriculum_id,
            semester=0,
            type=item.type,
            category_type=item.category_type,
            description=item.description,
            sort_order=item.sort_order
        )

    # copy CLO & CLOSummary
    for course in Course.objects.using('default').filter(curriculum_id=curriculum_id):
        new_course = example_to_real_course.get(course.id)
        if not new_course:
            continue

        for clo in CLO.objects.using('default').filter(course=course):
            CLO.objects.using('real').create(
                course=new_course,
                index=clo.index,
                clo=clo.clo,
                bloom=clo.bloom,
                k=clo.k,
                s=clo.s,
                e=clo.e,
                c=clo.c
            )

        summary = CLOSummary.objects.using('default').filter(course=course).first()
        if summary:
            CLOSummary.objects.using('real').create(
                course=new_course,
                bloom_score=summary.bloom_score,
                k_percent=summary.k_percent,
                s_percent=summary.s_percent,
                e_percent=summary.e_percent,
                c_percent=summary.c_percent
            )

    messages.success(request, "✅ Restored from example database to the main database (overwrote old data).")
    return redirect('credit_table', curriculum_id=curriculum_id)


def download_all_databases(request):
    filenames = ['real.sqlite3', 'example.sqlite3']
    missing_files = [f for f in filenames if not os.path.exists(f)]

    if missing_files:
        return HttpResponseNotFound(f"Missing files: {', '.join(missing_files)}")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename in filenames:
            zip_file.write(filename)

    zip_buffer.seek(0)
    return FileResponse(zip_buffer, as_attachment=True, filename='all_databases.zip')

def download_database(request, db_name):
    if db_name not in ['real', 'example']:
        return HttpResponse("Invalid database name", status=400)

    file_path = f'{db_name}.sqlite3'
    if not os.path.exists(file_path):
        return HttpResponse("File not found", status=404)

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f'{db_name}.sqlite3')

def sync_plo_credits_to_creditrow(curriculum):
    # update only in real (edit mode)
    plo_rows = CreditRow.objects.using('real').filter(curriculum=curriculum, row_type='plo')
    for row in plo_rows:
        if ':' in row.name:
            plo_tag = row.name.split(':')[0].strip()
        else:
            plo_tag = row.name.strip()
        new_credits = []
        for sem in range(1, 9):
            total = Course.objects.using('real').filter(
                curriculum=curriculum,
                semester=sem,
                plo__startswith=plo_tag
            ).aggregate(Sum('credits'))['credits__sum'] or 0
            new_credits.append(total)
        for i, val in enumerate(new_credits):
            setattr(row, f'credits_sem{i+1}', val)
        row.save(using='real')

def debug_print_plo_credits(curriculum):
    plo_rows = CreditRow.objects.using('real').filter(curriculum=curriculum, row_type='plo')
    print("\n====== DEBUG: PLO credits_sem1-8 ======")
    for row in plo_rows:
        print(f"{row.name:40s} | ", end='')
        print(" ".join([str(getattr(row, f'credits_sem{i}')) for i in range(1, 9)]))
    print("=======================================\n")


def plo_graph_from_creditrow(request, curriculum_id):
    mode = request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    # Get PLO rows
    plo_rows = CreditRow.objects.using(db).filter(curriculum_id=curriculum_id, row_type='plo').order_by('id')
    plo_labels = []
    plo_values = []
    for row in plo_rows:
        tag = row.name.split(':')[0].strip()
        plo_labels.append(tag)
        plo_values.append([
            row.credits_sem1, row.credits_sem2, row.credits_sem3, row.credits_sem4,
            row.credits_sem5, row.credits_sem6, row.credits_sem7, row.credits_sem8,
        ])

    # Handle no data
    if len(plo_labels) == 0:
        plt.figure(figsize=(10, 5))
        plt.axis('off')
        plt.text(0.5, 0.5, 'No PLO data available for graph', fontsize=28, color='red',
                 ha='center', va='center', transform=plt.gca().transAxes)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return HttpResponse(buf.getvalue(), content_type='image/png')

    # Prepare year sums
    plo_values = np.array(plo_values).T   # shape: (8, n_plo)
    year_labels = ['Year 1', 'Year 2', 'Year 3', 'Year 4']
    year_data = [
        plo_values[0] + plo_values[1],   # Year 1
        plo_values[2] + plo_values[3],   # Year 2
        plo_values[4] + plo_values[5],   # Year 3
        plo_values[6] + plo_values[7],   # Year 4
    ]

    ind = np.arange(len(plo_labels))
    bottom = np.zeros(len(plo_labels))
    colors = ['#43a047', '#1976d2', '#fbc02d', '#d81b60']

    plt.figure(figsize=(12, 5))
    for i in range(4):
        plt.bar(ind, year_data[i], bottom=bottom, label=year_labels[i], color=colors[i])
        bottom += year_data[i]
    plt.xticks(ind, plo_labels)
    plt.xlabel('PLO')
    plt.ylabel('Total Credits')
    plt.title('PLO Credit Distribution by Year (Stacked Bar)')
    plt.legend(title="Year")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')
