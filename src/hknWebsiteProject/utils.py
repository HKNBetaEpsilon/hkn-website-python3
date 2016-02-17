from users.models import Member

def has_complete_profile(uniqname):
	# check all aspects of a profile to make sure that it is complete
	m = Member.objects.get(uniqname = uniqname)
	if m.first_name and m.last_name and m.resume and m.profile_pic and m.major and m.edu_level and m.expected_grad_date:
		return True
	return False

def get_members_with_complete_profile():
	members_comp_prof = Member.objects.filter(first_name__isnull=False)
	members_comp_prof = members_comp_prof.exclude(first_name__exact="")
	members_comp_prof = members_comp_prof.filter(last_name__isnull=False)
	members_comp_prof = members_comp_prof.exclude(last_name__exact="")
	members_comp_prof = members_comp_prof.filter(major__isnull=False)
	members_comp_prof = members_comp_prof.filter(edu_level__isnull=False)
	members_comp_prof = members_comp_prof.filter(expected_grad_date__isnull=False)
	members_comp_prof = members_comp_prof.exclude(profile_pic__exact="")
	members_comp_prof = members_comp_prof.filter(resume__isnull=False)
	members_comp_prof = members_comp_prof.exclude(resume__exact="")
	return members_comp_prof

def get_members_with_uncomplete_profile():
	members = Member.objects.all()
	members_uncomp_prof = []
	for m in members:
		if not (m.first_name and m.last_name and m.resume and m.profile_pic and m.major and m.edu_level and m.expected_grad_date):
			members_uncomp_prof.append(m)
	return members_uncomp_prof
