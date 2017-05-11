from connectwise.member import Member


me = Member.fetch_member_by_office_email('nick.alexander@cecillinois.org')
# me = Member.fetch_member_by_identifier('NAlexander')
print(me.firstName)
print(me.lastName)
print(me.identifier)
print(me.officeEmail)