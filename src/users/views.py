from hknWebsiteProject import settings
from django.contrib.auth.decorators import login_required

import collections
from string import ascii_uppercase

import os
from django.conf import settings
from django.shortcuts import render, redirect

# Create your views here.
from .models import Member
from .forms import MemberForm
from electeeManagement.models import Electee, Requirements, Social, Service_Hours
from hknWebsiteProject.resume_zip import zip_resumes
from hknWebsiteProject.utils import get_current_members_with_completed_profile, \
    get_alumni_with_completed_profile, \
    has_complete_profile


def make_alpha_dict(members):
    alpha_list = collections.OrderedDict()
    # separate member list by letter first name starts with in order to display
    # 	members in these groupings
    for letter in ascii_uppercase:
        member_list = members.filter(first_name__startswith=letter)
        member_list = member_list.order_by('first_name', 'last_name')
        if member_list:
            alpha_list[letter] = member_list

    return alpha_list


@login_required()
def member_list(request):
    # displays the list of all undergrad/grad members who have a complete profile
    member_list = make_alpha_dict(get_current_members_with_completed_profile())

    context = {
        'member_list': member_list,
    }

    return render(request, "users/member_list.html", context)


@login_required()
def alumni_list(request):
    # displays the list of all alumni members who have a complete profile
    alumni_list = make_alpha_dict(get_alumni_with_completed_profile())

    context = {
        'alumni_list': alumni_list,
    }

    return render(request, "users/alumni_list.html", context)


@login_required()
def profile(request, uniqname, profile_saved=0):
    context = {}
    is_curr_user = (request.user.username == uniqname)

    m = Member.objects.get(uniqname=uniqname)
    logged_in_as = Member.objects.get(uniqname=request.user.username)

    electee_progress = m.is_electee() and (is_curr_user or request.user.is_superuser or logged_in_as.is_officer())

    if electee_progress:
        e = Electee.objects.get(member_id=uniqname)

        progress = {
            'uniqname': e.member.uniqname,
            'first_name': e.member.first_name,
            'last_name': e.member.last_name,

            'num_socials_approved': e.num_socials_approved,
            'num_socials_total' : e.num_socials_total,
            'num_service_hours_approved': e.num_service_hours_approved,
            'num_service_hours_total' : e.num_service_hours_total,
            'num_service_hours_db' : e.num_service_hours_db,
            'num_service_hours_tutoring' : e.num_service_hours_tutoring,
            'num_service_hours_hkn' : e.num_service_hours_hkn,
            'num_service_hours_external' : e.num_service_hours_external,
            'electee_interview': e.electee_interview,
            'electee_exam': e.electee_exam,
            'dues': e.dues,
            'general_meetings_missed' : e.general_meetings_missed,
        }

        requirements = dict((requirements.requirement, requirements) for requirements in
                            Requirements.objects.all())
        socials = Social.objects.filter(electee_id=uniqname).order_by('-timestamp')
        projects = Service_Hours.objects.filter(electee_id=uniqname).order_by('-timestamp')

        req_social, req_service = ('A_UG_SOCIAL', 'C_UG_TOTAL_HOURS') if \
            e.member.is_undergraduate() else ('B_G_SOCIAL', 'D_G_TOTAL_HOURS')

        progress['social_req'] = requirements[req_social].num_required
        progress['service_req'] = requirements[req_service].num_required

        context = {
            'e': progress,
            'requirements': requirements,
            'submit': False,
            'socials': socials,
            'projects': projects,
        }

        # if the request user is viewing their own electee progress,
        # 	show the buttons to submit socials and service hours
        if (uniqname == request.user.username) and has_complete_profile(uniqname):
            context['submit'] = True

    context['profile'] = m
    context['is_curr_user'] = is_curr_user
    context['profile_saved'] = profile_saved
    context['electee_progress'] = electee_progress

    return render(request, "users/profile.html", context)


@login_required()
def profile_edit(request, uniqname):
    context = {}
    is_curr_user = (request.user.username == uniqname)
    if not is_curr_user:
        context = {
            'error': True,
            'error_msg': 'You cannot edit this profile'
        }
    else:
        context['profile_saved'] = False

        m = Member.objects.get(uniqname=uniqname)
        logged_in_as = Member.objects.get(uniqname=request.user.username)
        form = MemberForm(instance=m)

        old_pic_url = None
        old_resume_url = None

        if m.profile_pic:
            old_pic_url = settings.MEDIA_ROOT + '/' + '/'.join(m.profile_pic.url.split('/')[2:])

        if m.resume:
            old_resume_url = settings.MEDIA_ROOT + '/' + '/'.join(m.resume.url.split('/')[2:])

        if request.POST:
            form = MemberForm(request.POST, request.FILES, instance=m)

            if form.is_valid():
                # import ipdb; ipdb.set_trace()
                if request.FILES.get('profile_pic') and old_pic_url:
                    os.remove(old_pic_url)
                if (request.FILES.get('resume') or request.POST.get(
                        'resume-clear') == 'on') and old_resume_url:
                    os.remove(old_resume_url)

                form.save()
                zip_resumes()

                return redirect('profile', uniqname=uniqname, profile_saved=1)

        context['form'] = form

    return render(request, "users/profile_edit.html", context)
