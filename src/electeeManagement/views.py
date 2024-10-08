from hknWebsiteProject import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage

# Create your views here.

from users.forms import Member
from .forms import SocialForm, ServiceHoursForm
from .models import Electee, Social, Service_Hours, Requirements
from hknWebsiteProject.utils import is_officer

from django.forms import modelformset_factory


def update_approved_hours():
    all_electees = Electee.objects.all()
    for e in all_electees:
        e.num_socials_approved = Social.objects.filter(electee=e).filter(approved='1').count()

        requirements = dict(
            (requirements.requirement, requirements) for requirements in Requirements.objects.all())
        max_db, max_dt, max_ex = ('E_UG_DB_HOURS', 'G_UG_DT_HOURS', 'I_UG_EXTERNAL_HOURS') if \
                    e.member.is_undergraduate() else ('F_G_DB_HOURS', 'H_G_DT_HOURS', 'J_G_EXTERNAL_HOURS')

        e.num_service_hours_approved = 0
        num_db_hours = 0
        num_tutoring_hours = 0
        num_ex_hours = 0
        num_hkn_hours = 0
        service_hours = Service_Hours.objects.filter(electee=e).filter(approved='1')
        for event in service_hours:
            if event.service_type == 'dB':
                num_db_hours += event.num_hours
            elif event.service_type == 'HKN':
                num_hkn_hours += event.num_hours
            elif event.service_type == 'DT':
                num_tutoring_hours += event.num_hours
            else: #event.service_type == 'Ex':
                num_ex_hours += event.num_hours
        if num_db_hours > requirements[max_db].num_required:
            num_db_hours = requirements[max_db].num_required
        if num_ex_hours > requirements[max_ex].num_required:
            num_ex_hours = requirements[max_ex].num_required
        if num_tutoring_hours > requirements[max_dt].num_required:
            num_tutoring_hours = requirements[max_dt].num_required
        e.num_service_hours_approved = num_db_hours + num_ex_hours + num_hkn_hours + num_tutoring_hours
        e.save()


@login_required()
def all_electees(request):
    context = {}
    m =  Member.objects.get(uniqname=request.user.username)
    if not (request.user.is_superuser or is_officer(request.user.username)):
        context = {
            'error': True,
            'error_msg': 'You do not have permission to access this page'
        }
    else:
        # get all of the electee objects to display
        electee_list = Electee.objects.filter(member__status='E')
        requirements = dict(
            (requirements.requirement, requirements) for requirements in Requirements.objects.all())

        # process the electee progress, so that wo don't have to run those if-else in template html
        electee_list_plain = []
        total_hours = 0
        for electee in electee_list:
            progress = {
                'uniqname': electee.member.uniqname,
                'first_name': electee.member.first_name,
                'last_name': electee.member.last_name,

                'num_socials_approved': electee.num_socials_approved,
                'num_service_hours_approved': electee.num_service_hours_approved,
                'electee_interview': electee.electee_interview,
                'electee_exam': electee.electee_exam,
                'dues': electee.dues,
            }
            total_hours += electee.num_service_hours_approved

            # check for if requirement meets
            req_social, req_service = ('A_UG_SOCIAL', 'C_UG_TOTAL_HOURS') if \
                electee.member.is_undergraduate() else ('B_G_SOCIAL', 'D_G_TOTAL_HOURS')

            progress['social_req'] = requirements[req_social].num_required
            progress['service_req'] = requirements[req_service].num_required

            progress['social_done'] = (
                progress['num_socials_approved'] >= progress['social_req'])
            progress['service_done'] = (
                progress['num_service_hours_approved'] >= progress['service_req'])

            # decide if the electee are able to convert to active
            progress['convert'] = progress['social_done'] and progress['service_done'] and progress[
                'electee_interview'] and progress['electee_exam'] and progress['dues']

            electee_list_plain.append(progress)

        context['electee_list'] = electee_list_plain
        context['total_hours'] = total_hours

    return render(request, "electeeManagement/all_electees.html", context)


@login_required()
def submit_social(request):
    m = Member.objects.get(uniqname=request.user.username)
    # error if the request user is anonymous or not an electee
    if not m.is_electee():
        context = {
            'error': True,
            'error_msg': 'You must be an electee to submit socials'
        }
    else:
        context = {
            'error': False,
            'social_submitted': False
        }

        form = SocialForm(request.POST or None)
        if request.POST:
            if form.is_valid():
                social = form.save(commit=False)
                # set the electee field on the social model
                social.electee = Electee.objects.get(member_id=request.user.username)
                social.save()

                electee = Electee.objects.get(member_id=request.user.username)
                electee.num_socials_total = electee.num_socials_total + 1
                electee.save()

                # display a new blank form
                form = SocialForm(None)

                # show green bar at top of page saying that a social has been submitted
                context['social_submitted'] = True

        context['form'] = form

    return render(request, "electeeManagement/submit_social.html", context)


@login_required()
def submit_service_hours(request):
    m = Member.objects.get(uniqname=request.user.username)
    # error if the request user is anonymous or not an electee
    if not m.is_electee():
        context = {
            'error': True,
            'error_msg': 'You must be an electee to submit service hours'
        }
    else:
        context = {
            'error': False,
            'service_hours_submitted': False
        }
        requirements = dict(
            (requirements.requirement, requirements) for requirements in Requirements.objects.all())
        form = ServiceHoursForm(request.POST or None)
        if request.POST:
            if form.is_valid():
                service_hours = form.save(commit=False)
                # set the electee field on the service_hours model
                service_hours.electee = Electee.objects.get(member_id=request.user.username)
                service_hours.save()

                electee = Electee.objects.get(member_id=request.user.username)
                max_db, max_dt, max_ex = ('E_UG_DB_HOURS', 'G_UG_DT_HOURS', 'I_UG_EXTERNAL_HOURS') if \
                    electee.member.is_undergraduate() else ('F_G_DB_HOURS', 'H_G_DT_HOURS', 'J_G_EXTERNAL_HOURS')
                electee.num_service_hours_total = electee.num_service_hours_total + service_hours.num_hours
                if service_hours.service_type == 'dB':
                    electee.num_service_hours_db = electee.num_service_hours_db + service_hours.num_hours
                    if electee.num_service_hours_db > requirements[max_db].num_required:
                        electee.num_service_hours_db = requirements[max_db].num_required
                elif service_hours.service_type == 'HKN':
                    electee.num_service_hours_hkn = electee.num_service_hours_hkn + service_hours.num_hours
                elif service_hours.service_type == 'DT':
                    electee.num_service_hours_tutoring = electee.num_service_hours_tutoring + service_hours.num_hours
                    if electee.num_service_hours_tutoring > requirements[max_dt].num_required:
                        electee.num_service_hours_tutoring = requirements[max_dt].num_required
                else:
                    electee.num_service_hours_external = electee.num_service_hours_external + service_hours.num_hours
                    if electee.num_service_hours_external > requirements[max_ex].num_required:
                        electee.num_service_hours_external = requirements[max_ex].num_required
                electee.save()

                # display a new blank form
                form = ServiceHoursForm(None)

                # show green bar at top of page saying that a service hours have been submitted
                context['service_hours_submitted'] = True

        context['form'] = form
        context['max_hours_per_event'] = requirements['K_SINGLE_SERVICE_EVENT_HOURS'].num_required

    return render(request, "electeeManagement/submit_service_hours.html", context)


# shows a list of all unapporved socials and service hours
@login_required()
def electee_submission_approval(request, approved=0):
    context = {}
    if not (request.user.is_superuser or is_officer(request.user.username)):
        context = {
            'error': True,
            'error_msg': 'You do not have permission to access this page'
        }
    else:
        # get all unapproved socials and service hours
        social_list = Social.objects.filter(approved='0')
        service_hour_list = Service_Hours.objects.filter(approved='0')

        SocialFormSet = modelformset_factory(Social, fields=('approved',), extra=0)
        social_formset = SocialFormSet(
            queryset=Social.objects.filter(approved='0').order_by('timestamp'))

        ServiceFormSet = modelformset_factory(Service_Hours, fields=('approved',), extra=0)
        service_formset = ServiceFormSet(
            queryset=Service_Hours.objects.filter(approved='0').order_by('timestamp'))

        context = {
            'social_list': social_list,
            'service_hour_list': service_hour_list,
            'social_formset': social_formset,
            'service_formset': service_formset,
            'approved': approved
        }

        if request.POST:
            formset = SocialFormSet(request.POST)
            if formset.is_valid():
                formset.save()
                update_approved_hours()
            formset = ServiceFormSet(request.POST)
            if formset.is_valid():
                formset.save()
                update_approved_hours()
            return redirect('electee_submission_approval', approved=1)

    return render(request, "electeeManagement/electee_submission_approval.html", context)


@login_required()
def edit_electee_requirements(request):
    context = {}
    if not (request.user.is_superuser or is_officer(request.user.username)):
        context = {
            'error': True,
            'error_msg': 'You do not have permission to access this page'
        }
    else:
        RequirementsFormset = modelformset_factory(Requirements, fields=('num_required',), extra=0)
        req_formset = RequirementsFormset(queryset=Requirements.objects.all())

        context = {
            'req_formset': req_formset,
            'requirement_changed': False
        }

        if request.POST:
            formset = RequirementsFormset(request.POST)
            formset.save()
            context['requirement_changed'] = True

    return render(request, "electeeManagement/edit_electee_requirements.html", context)


@login_required()
def initilize_electee_requirements(request):
    context = {}
    if not request.user.is_superuser:
        context = {
            'error': True,
            'error_msg': 'You do not have permission to access this page'
        }
    else:
        context = {
            'submitted': False
        }

        if request.POST:
            a = Requirements(requirement='A_UG_SOCIAL', num_required=0)
            a.save()
            b = Requirements(requirement='B_G_SOCIAL', num_required=0)
            b.save()
            c = Requirements(requirement='C_UG_TOTAL_HOURS', num_required=0)
            c.save()
            d = Requirements(requirement='D_G_TOTAL_HOURS', num_required=0)
            d.save()
            e = Requirements(requirement='E_UG_DB_HOURS', num_required=0)
            e.save()
            f = Requirements(requirement='F_G_DB_HOURS', num_required=0)
            f.save()
            g = Requirements(requirement='G_UG_DT_HOURS', num_required=0)
            g.save()
            h = Requirements(requirement='H_G_DT_HOURS', num_required=0)
            h.save()
            i = Requirements(requirement='I_UG_EXTERNAL_HOURS', num_required=0)
            i.save()
            j = Requirements(requirement='J_G_EXTERNAL_HOURS', num_required=0)
            j.save()
            k = Requirements(requirement='K_SINGLE_SERVICE_EVENT_HOURS', num_required=0)
            k.save()

            context['submitted'] = True

    return render(request, "electeeManagement/initilize_electee_requirements.html", context)


@login_required()
def electee_turn_ins(request):
    context = {}
    if not (request.user.is_superuser or is_officer(request.user.username)):
        context = {
            'error': True,
            'error_msg': 'You do not have permission to access this page'
        }
    else:
        TurnInsFormset = modelformset_factory(Electee,
                                              fields=('electee_interview', 'dues', 'electee_exam'),
                                              extra=0)
        turnins_formset = TurnInsFormset(queryset=Electee.objects.all())
        context = {
            'turnins_formset': turnins_formset
        }

        if request.POST:
            formset = TurnInsFormset(request.POST)
            formset.save()
            context['turnins_saved'] = True

    return render(request, "electeeManagement/electee_turn_ins.html", context)


@login_required()
def convert(request, uniqname):
    if request.user.is_superuser or is_officer(request.user.username):
        if request.POST:
            member = Member.objects.get(uniqname=uniqname)
            if member.status == 'E':
                member.status = 'A'
                member.save()
                electee = Electee.objects.get(member=member)
                # Create Email to document completed requirements
                # subject = '[HKN] Electee has been converted to Active'
                # message = '''{} has been converted to an active! Here is a summary of their hours and socials:
                
                # Hours:
                # Drop-In Tutoring - 0
                # dB Cafe - {}
                # '''.format(uniqname, 0)

                # electee.delete()
    return redirect(request.META.get('HTTP_REFERER'), None, None)


@login_required()
def remove_electee(request, uniqname):
    if request.user.is_superuser or is_officer(request.user.username):
        if request.POST:
            member = Member.objects.get(uniqname=uniqname)
            member.delete()
    return redirect(request.META.get('HTTP_REFERER'), None, None)

