from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from table.models import Curriculum
import shutil
import os


@staff_member_required
def sync_real_to_example(request):
    """
    Admin-only function to synchronize the entire real.sqlite3 database
    into example.sqlite3. This operation fully overwrites the example database
    with the current real database contents.
    """
    status = ""
    if request.method == "POST":
        try:
            source = os.path.join(os.path.dirname(__file__), '..', 'real.sqlite3')
            dest = os.path.join(os.path.dirname(__file__), '..', 'example.sqlite3')
            shutil.copyfile(source, dest)
            status = "✅ Sync completed successfully. Data copied from real → example."
        except Exception as e:
            status = f"❌ Error occurred during sync: {str(e)}"

    return render(request, 'admin/sync_real_to_example.html', {'status': status})


@staff_member_required
def sync_curriculum_example_to_real(request, curriculum_id):
    """
    Admin-only function to synchronize a single curriculum record
    from the example (default) database to the real (editable) database.

    Args:
        request: Django HttpRequest object
        curriculum_id: ID of the curriculum to be synchronized
    """
    status = ""
    try:
        # Retrieve the curriculum from the example (default) database
        example_curriculum = Curriculum.objects.using('default').get(pk=curriculum_id)

        # Update or create the corresponding record in the real database
        Curriculum.objects.using('real').update_or_create(
            pk=example_curriculum.pk,
            defaults={
                'name': example_curriculum.name,
                # Add other fields here if needed, e.g.:
                # 'description': example_curriculum.description,
            }
        )

        status = f"✅ Successfully synced Curriculum ID {curriculum_id} to the real database."

    except Curriculum.DoesNotExist:
        status = f"❌ Curriculum ID {curriculum_id} not found in the example database."
    except Exception as e:
        status = f"❌ Error during synchronization: {str(e)}"

    return render(request, 'admin/sync_result.html', {'status': status})
