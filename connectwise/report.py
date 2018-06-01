import re
import unicodedata
from datetime import date, datetime, timezone
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, Table, TableStyle, KeepTogether


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def hours_to_days(hours):
    if hours == 0:
        return 'Full Day'
    elif hours <= 2:
        return 'Quarter Day'
    elif hours <= 4:
        return 'Half Day'
    elif hours < 16:
        return 'Full Day'
    elif hours >= 16:
        return str(round(hours / 8, 2)) + ' Days'


class Report:
    def __init__(self, name, filters, sort):
        self.name = name
        self.filters = filters
        self.sort = sort

    def __repr__(self):
        return "<Report {}>".format(self.name)

    @staticmethod
    def clean_str(value):
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        value = re.sub(r'[-\s]+', '-', value)
        return value

    def _generate_report_content(self):
        pass  # either modify this or create a subclass for each report type and override this method there

    def get_dateframe(self, on_or_after, before):
        """
        Dates can be either datetime objects or strings
        """
        if isinstance(on_or_after, str): on_or_after = datetime.strptime(on_or_after, '%Y-%m-%d')
        if isinstance(before, str): before = datetime.strptime(before, '%Y-%m-%d')
        if not before:
            before = datetime.today()

        if on_or_after.day == 1 and (on_or_after + relativedelta(months=1)).strftime('%Y%m%d') == before.strftime('%Y%m%d'):
            month = on_or_after.strftime('%B %Y')
        else:
            month = '{} to {}'.format(on_or_after.strftime('%b %-d, %Y'), (before - relativedelta(days=1)).strftime('%b %-d, %Y'))
        return month

    def format_month(self, on_or_after, before):
        on_or_after = datetime.strptime(on_or_after, '%Y-%m-%d')
        if on_or_after.day == 1 and (on_or_after + relativedelta(months=1)).strftime('%Y-%m-%d') == before:
            return on_or_after.strftime('%B %Y')
        return None

    def save_pdf(self):
        doc = SimpleDocTemplate(
            "output/{}/{} Report.pdf".format(self.output_subdir, self.name),
            pagesize=letter,
            rightMargin=36, leftMargin=36,
            topMargin=72, bottomMargin=40)
        Story = self._generate_report_content()
        doc.build(Story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

    def _header_footer(self, canvas, doc):
        # Save the state of our canvas so we can draw on it
        canvas.saveState()
        styles = getSampleStyleSheet()

        # Header
        header_text = '<font size=8>'
        header_text += '<strong>Date Run:</strong> {}'.format(datetime.today().strftime('%Y-%m-%d at %-I:%M%p'))
        if self.filters:
            header_text += '<br /><strong>Filters:</strong> {}'.format(' - '.join(['{}: {}'.format(k, v) for k, v in self.filters.items()]))
        if self.sort:
            header_text += '<br /><strong>Sort:</strong> By {}'.format(self.sort.title())
        header_text += '</font>'

        header = Paragraph(header_text, styles['Normal'])

        # header = Paragraph(
        #     '<font size=8><strong>Date Run:</strong> {}<br />'
        #     '<strong>Filters:</strong> {}<br />'
        #     '<strong>Sort:</strong> By {}</font>'.format(
        #         datetime.today().strftime('%Y-%m-%d at %-I:%M%p'),
        #         ' - '.join(['{}: {}'.format(k, v) for k, v in self.filters.items()]),
        #         self.sort
        #     ), styles['Normal'])

        w, h = header.wrap(doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)

        # Footer
        footer = Paragraph('© {} Consortium for Education Change. All rights reserved.'.format(date.today().year),
                           styles['Normal'])
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h + 16)

        # Release the canvas
        canvas.restoreState()


class UpcomingSchedule(Report):
    def __init__(self, schedule_entries, filters, sort='dateStart'):
        self.schedule_entries = schedule_entries
        self.filters = filters
        self.sort = sort
        self.name = 'Upcoming Schedule'
        self.output_subdir = 'ConnectWise'

    def save_pdf(self):
        doc = SimpleDocTemplate(
            "output/{}/{} By {} Report.pdf".format(self.output_subdir, self.name, self.sort),
            pagesize=letter,
            rightMargin=36, leftMargin=36,
            topMargin=72, bottomMargin=40)
        Story = self._generate_report_content()
        doc.build(Story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

    def _generate_report_content(self):
        Story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        logo = "static/img/BeyondComplianceAdminAcademyStorylineLogoHighRes.gif"
        titletext = "{} By {} Report<br />{} Team".format(self.name, self.sort, self.filters['Team'])
        # description_text = "This is a schedule report"

        im = Image(logo, 2 * inch, 0.84 * inch)

        count_consultants = len(set([schedule_entry.member['identifier'] for schedule_entry in self.schedule_entries]))
        count_companies = len(set([schedule_entry.name.split(' / ')[0] for schedule_entry in self.schedule_entries]))

        # Story.append(im)
        Story.append(Spacer(1, 12))
        Story.append(Paragraph(titletext, styles["Title"]))
        Story.append(Spacer(1, 12))
        Story.append(Paragraph('Schedule Entries: {}'.format(len(self.schedule_entries)), styles["Normal"]))
        Story.append(Paragraph('Consultants Scheduled: {}'.format(count_consultants), styles["Normal"]))
        Story.append(Paragraph('Districts: {}'.format(count_companies), styles["Normal"]))



        # schedule_table = [[
        #     Paragraph('<strong>Date</strong>', styles["Normal"]),
        #     Paragraph('<strong>Consultant</strong>', styles["Normal"]),
        #     Paragraph('<strong>District/Project/Phase(s)/Ticket</strong>', styles["Normal"])
        # ]]

        # sorted_schedule_entries = sorted(self.schedule_entries, key=lambda x: x.member['identifier'][1:])
        sorted_schedule_entries = sorted(self.schedule_entries, key=attrgetter('dateStart'))
        if self.sort.lower() == 'consultant':
            # sorted_schedule_entries = sorted(sorted_schedule_entries, key=lambda x: x.member['identifier'][1:])
            member_identifiers = sorted(
                set([schedule_entry.member['identifier'] for schedule_entry in sorted_schedule_entries]))
            for member_identifier in member_identifiers:
                schedule_table = []
                for schedule_entry in sorted(self.schedule_entries, key=attrgetter('dateStart')):
                    if schedule_entry.member['identifier'] == member_identifier:
                        schedule_name_arr = schedule_entry.name.split(' / ')
                        company = schedule_name_arr.pop(0)
                        schedule_name = ' / '.join(schedule_name_arr)
                        schedule_table.append(
                            [Paragraph('{}<br />{}'.format(
                                utc_to_local(
                                    datetime.strptime(schedule_entry.dateStart, '%Y-%m-%dT%H:%M:%SZ')).strftime(
                                    '%b %-d, %-I:%M%p'),
                                hours_to_days(schedule_entry.hours)
                            ), styles["Normal"]),
                                Paragraph(company, styles["Normal"]),
                                Paragraph('<font size=9>%s</font>' % schedule_name, styles["Normal"])]
                        )
                t = Table(schedule_table, [1.3 * inch, 1.6 * inch, 4.3 * inch])
                t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                       ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                       ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                       ]))

                number_of_entries = '{} Schedule Entries'.format(len(schedule_table)) if len(schedule_table) > 1 else '1 Schedule Entry'

                member_section = []
                member_section.append(Spacer(1, 12))
                member_section.append(Paragraph('<strong>{}</strong> - {}:'.format(member_identifier, number_of_entries), styles["Normal"]))
                member_section.append(Spacer(1, 4))
                member_section.append(t)
                Story.append(KeepTogether(member_section))

        elif self.sort.lower() == 'date' or self.sort.lower() == 'month':
            months = sorted(set(
                [utc_to_local(datetime.strptime(schedule_entry.dateStart, '%Y-%m-%dT%H:%M:%SZ')).strftime('%Y-%-m-1')
                 for schedule_entry in sorted_schedule_entries]))

            for month in months:
                month_table = []
                for schedule_entry in sorted(self.schedule_entries, key=attrgetter('dateStart')):
                    schedule_name = schedule_entry.name.split(' / ')
                    schedule_company_name = schedule_name.pop(0)
                    schedule_name = ' / '.join(schedule_name)
                    if month == utc_to_local(
                            datetime.strptime(schedule_entry.dateStart, '%Y-%m-%dT%H:%M:%SZ')).strftime('%Y-%-m-1'):
                        month_table.append(
                            [Paragraph('{}<br />{}'.format(
                                utc_to_local(
                                    datetime.strptime(schedule_entry.dateStart, '%Y-%m-%dT%H:%M:%SZ')).strftime(
                                    '%b %-d, %-I:%M%p'),
                                hours_to_days(schedule_entry.hours)
                            ), styles["Normal"]),
                                Paragraph(schedule_entry.member['identifier'], styles["Normal"]),
                                Paragraph('<font size=9>%s</font>' % schedule_name, styles["Normal"])]
                        )
                        t = Table(month_table, [1.3 * inch, 1.2 * inch, 4.7 * inch])
                        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                               ]))
                        # Story.append(Paragraph('<strong>{}</strong>'.format(company_name), styles["Normal"]))

                number_of_entries = '{} Schedule Entries'.format(len(month_table)) if len(
                    month_table) > 1 else '1 Schedule Entry'

                Story.append(Spacer(1, 12))
                print(month)
                themonth = date(2017, int(month.split('-')[1]), 1).strftime('%B %Y')
                print(themonth)
                Story.append(Paragraph('<strong>{}</strong> - {}:'.format(themonth, number_of_entries), styles["Normal"]))
                Story.append(Spacer(1, 4))
                Story.append(t)
                # Story.append(company_section)
                # Story.append(KeepTogether(company_section))

        elif self.sort.lower() == 'district' or self.sort.lower() == 'company' or self.sort.lower() == 'organization':
            company_names = sorted(
                set([schedule_entry.name.split(' / ')[0] for schedule_entry in sorted_schedule_entries]))
            for company_name in company_names:
                company_table = []
                for schedule_entry in sorted(self.schedule_entries, key=attrgetter('dateStart')):
                    schedule_name = schedule_entry.name.split(' / ')
                    schedule_company_name = schedule_name.pop(0)
                    schedule_name = ' / '.join(schedule_name)
                    if schedule_company_name == company_name:
                        company_table.append(
                            [Paragraph('{}<br />{}'.format(
                                utc_to_local(
                                    datetime.strptime(schedule_entry.dateStart, '%Y-%m-%dT%H:%M:%SZ')).strftime(
                                    '%b %-d, %-I:%M%p'),
                                hours_to_days(schedule_entry.hours)
                            ), styles["Normal"]),
                                Paragraph(schedule_entry.member['identifier'], styles["Normal"]),
                                Paragraph('<font size=9>%s</font>' % schedule_name, styles["Normal"])]
                        )
                        t = Table(company_table, [1.3 * inch, 1.2 * inch, 4.7 * inch])
                        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                               ]))
                # Story.append(Paragraph('<strong>{}</strong>'.format(company_name), styles["Normal"]))

                number_of_entries = '{} Schedule Entries'.format(len(company_table)) if len(
                    company_table) > 1 else '1 Schedule Entry'

                # company_section = []
                Story.append(Spacer(1, 12))
                Story.append(Paragraph('<strong>{}</strong> - {}:'.format(company_name, number_of_entries), styles["Normal"]))
                Story.append(Spacer(1, 4))
                Story.append(t)
                # Story.append(KeepTogether(company_section))
                # sorted_schedule_entries = sorted(sorted_schedule_entries, key=attrgetter('name'))
        else:
            sorted_schedule_entries = sorted(sorted_schedule_entries, key=attrgetter(self.sort))

        # schedule_table = []
        # for schedule_entry in sorted_schedule_entries:


        # [schedule_table.append(
        #     [
        #         Paragraph(
        #             '{}<br />{}'.format(
        #                 utc_to_local(datetime.strptime(schedule_entry.dateStart, '%Y-%m-%dT%H:%M:%SZ')).strftime('%b %-d, %-I:%M%p'),
        #                 hours_to_days(schedule_entry.hours)
        #             ), styles["Normal"]),
        #         Paragraph(schedule_entry.member['identifier'], styles["Normal"]),
        #         Paragraph('<font size=9>%s</font>' % schedule_entry.name, styles["Normal"])
        #     ]) for schedule_entry in sorted_schedule_entries
        # ]
        #
        # t = Table(schedule_table, [1.2 * inch, 1 * inch, 5 * inch])
        # t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
        #                        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        #                        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        #                        ]))

        # for schedule_entry in self.schedule_entries:
        #     Story.append(
        #         Paragraph(schedule_entry.name, styles["Normal"])
        #     )

        # Story.append(Paragraph(description_text, styles["Normal"]))
        Story.append(Spacer(1, 12))
        # Story.append(t)
        return Story
