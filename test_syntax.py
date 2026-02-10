#!/usr/bin/env python
# Test file to check syntax
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

@login_required
def test_function(request):
    """Test function to check syntax."""
    try:
        parent_profile = request.user.parent_profile
        child = get_object_or_404(Child, id=1, parent=parent_profile)
        
        if request.method == 'POST':
            # Handle form submission
            child.name = request.POST.get('name')
            child.grade = request.POST.get('grade')
            if request.POST.get('reading_wpm'):
                child.reading_wpm = int(request.POST.get('reading_wpm'))
            if request.POST.get('reading_accuracy'):
                child.reading_accuracy = float(request.POST.get('reading_accuracy'))
            
            child.save()
            messages.success(request, f'{child.name}\'s details updated successfully!')
            return redirect('portal:profile')
        
        # GET request - show edit form
        return render(request, 'portal/edit_child.html', {
            'child': child,
            'grades': Child.GRADE_CHOICES,
        })
    
    except Child.DoesNotExist:
        messages.error(request, 'Child not found')
        return redirect('portal:profile')
    except Exception as e:
        messages.error(request, f'Error updating child: {str(e)}')
        return redirect('portal:profile')
