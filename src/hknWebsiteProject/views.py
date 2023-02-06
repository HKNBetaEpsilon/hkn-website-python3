from datetime import date

from electeeManagement.models import Electee, Requirements
from electeeManagement.views import all_electees
from hknWebsiteProject import settings
from django.contrib.auth.decorators import login_required
from users.forms import NewMemberForm
from users.models import Member

from django.contrib.auth.models import User, AnonymousUser
from django.core.mail import EmailMessage
from django.shortcuts import render
from .utils import has_complete_profile, get_members_with_complete_profile, \
    get_members_with_uncomplete_profile


class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def home(request, bad_user=False):
    context = {}
    try:
        user_is_anonymous = request.user.is_anonymous()
    except TypeError:
        user_is_anonymous = request.user.is_anonymous
    if not user_is_anonymous:
        # display prompt to ask member to complete their profile
        if not has_complete_profile(request.user.username):
            context = {
                'has_not_complete_profile': True
            }

    elif bad_user:
        # Anonymous with an username:
        # The user tries to login but not a member
        context = {
            'not_member': True
        }
    return render(request, "hknWebsiteProject/home.html", context)


def about(request):
    return render(request, "hknWebsiteProject/about.html", {})


def corporate(request):
    return render(request, "hknWebsiteProject/corporate.html", {})


def make_members(form, electee):
    context = {}
    uniqnames = form.cleaned_data.get('new_members').lower().split(',')
    try:
        # validate each submitted uniqname to make sure that a member
        # 	with that uniqname does not already exist, and that it is
        # 	alphabetic and a valid number of characters
        for name in uniqnames:
            if Member.objects.filter(uniqname=name).exists():
                raise MyError('Uniqname already exists')
    except MyError:
        context = {
            'error': True,
            'error_msg': 'Uniqname ' + name + ' already exists! None added.'
        }
    else:
        # display message saying members were successfully submitted
        mail_list = []
        for name in uniqnames:
            m = Member(uniqname=name)
            if electee:
                m.status = 'E'
            else:
                m.status = 'A'
            m.save()

            if electee:
                Electee(member=m).save()

            subject = '[HKN] Welcome to the HKN Beta Epsilon Website'
            message = welcome_msg
            from_email = settings.EMAIL_HOST_USER
            to_email = [name + '@umich.edu']

            email = EmailMessage(subject, message, from_email)
            email.to = to_email
            email.cc = [from_email]
            email.send()

    return context


@login_required()
def create_new_members(request):
    context = {}

    form = NewMemberForm(request.POST or None)

    if form.is_valid():
        context = make_members(form,
                               form.cleaned_data.get('type') == 'E')
        form = NewMemberForm()
        if 'error' not in context:
            context['new_members_submitted'] = True

    context['form'] = form

    return render(request, "hknWebsiteProject/create_new_members.html", context)


def login_user(request):
    email = request.user.email
    email_base, provider = email.split('@')
    bad_user = False

    if (not provider == 'umich.edu') and (not email == 'dbcafehi@gmail.com'):
        request.user = badUser(request)
        bad_user = True
    else:
        try:
            m = Member.objects.get(uniqname=email_base)

            # If the user doesn't have name in their profile, default to the
            # name registered with their login info
            if not m.first_name:
                m.first_name = request.user.first_name
            if not m.last_name:
                m.last_name = request.user.last_name
            m.save()
        except Member.DoesNotExist:
            request.user = badUser(request)
            bad_user = True

    return home(request, bad_user)


def badUser(request):
    User.objects.get(username__exact=request.user).delete()
    return AnonymousUser()


welcome_msg = '''
Welcome to the HKN website! An account has been created for you.

Please go to hkn.eecs.umich.edu and log in with your umich account to complete your profile. Once you complete your profile, you will appear in the memeber list and you're resume will be included in the resume book.

Thanks,
HKN Website

This is an automated message please do not reply as this email is not checked. If you need assistance, please email hkn-webmaster@umich.edu
'''


@login_required()
def mentoring_competition(request):
    context = {}
    return render(request, "hknWebsiteProject/mentoring_competition.html", context)


@login_required()
def elections(request):
    context = {}
    return render(request, "hknWebsiteProject/elections.html", context)


@login_required()
def feedback(request):
    context = {}
    return render(request, "hknWebsiteProject/feedback.html", context)


@login_required()
def misc_tools(request, success=False):
    total_num_users = Member.objects.count()
    num_members_comp_prof = get_members_with_complete_profile().count()
    members = Member.objects.all()
    context = {
        'success': success,
        'total_num_users': total_num_users,
        'num_members_comp_prof': num_members_comp_prof,
        'members': members
    }
    return render(request, "hknWebsiteProject/misc_tools.html", context)


@login_required()
def email_uncompleted_profiles(request):
    members_wo_profile = get_members_with_uncomplete_profile()
    mail_list = []

    for m in members_wo_profile:
        subject = '[HKN] Reminder: Welcome to the HKN Beta Epsilon Website'
        message = 'Don\'t forget to complete your website profile!\n' + welcome_msg
        from_email = settings.EMAIL_HOST_USER
        to_email = [m.uniqname + '@umich.edu']

        email = EmailMessage(subject, message, from_email)
        email.to = to_email
        email.cc = [from_email]
        email.send()

    return misc_tools(request, True)


@login_required()
def make_alumni(request):
    so_old = date(1900, 1, 1)
    current_members = Member.objects.exclude(edu_level__exact='AL')
    current_members = current_members.filter(graduation_date__range=(so_old, date.today()))
    for m in current_members:
        m.edu_level = 'AL'
        m.save()

    return misc_tools(request, True)


@login_required
def email_electee_progress(request):
    electee_list = Electee.objects.filter(member__status='E')
    requirements = dict(
        (requirements.requirement, requirements) for requirements in Requirements.objects.all())
    
    mail_list = []

    for electee in electee_list:
        # Get requirements
        req_social, req_service = ('A_UG_SOCIAL', 'C_UG_TOTAL_HOURS') if \
            electee.member.is_undergraduate() else ('B_G_SOCIAL', 'D_G_TOTAL_HOURS')
        # Get interview status
        if electee.electee_interview:
            interview = 'COMPLETED'
        else:
            interview = 'NOT COMPLETED'
        # Get exam status
        if electee.electee_exam:
            exam = 'COMPLETED'
        else:
            exam = 'NOT COMPLETED'
        # Get dues status
        if electee.dues:
            dues = 'PAID'
        else:
            dues = 'NOT PAID'
        # Create email
        subject = '[HKN] Electee Progress Report'
        message = '''Dear {} {},

        This is an automatically generated report of your current progress towards electing into HKN.

        Completed Requirements:
        Socials: {}/{}
        Projects: {}/{}
        Electee Interview: {}
        Electee Exam: {}
        Paid Dues: {}

        If you have any questions about completing requirements or electing in general, email hkn-vp@umich.edu.
        If you no longer wish to join HKN, email hkn-officers@umich.edu.

        HKN
        '''.format( electee.member.first_name, electee.member.last_name,
                    electee.num_socials_approved, requirements[req_social].num_required,
                    electee.num_service_hours_approved, requirements[req_service].num_required,
                    interview, exam, dues)
        from_email = settings.EMAIL_HOST_USER
        to_email = [electee.member.uniqname + '@umich.edu']

        email = EmailMessage(subject, message, from_email)
        email.to = to_email
        email.cc = [from_email]
        email.send()

    return all_electees(request)

