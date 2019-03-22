from flask.ext.script import Command
from datetime import datetime, timedelta
import logging
from sqlalchemy import or_
from hipcooks import db
from hipcooks.models import Assistant, Schedule, GiftCertificate
from hipcooks.email import email_gift_certificate


logging.basicConfig(filename='/var/log/uwsgi/app/assistant_credit_cron.log',
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')


class AssistantCreditAndGiftCertificateAward(Command):
    """
    Awards a credit to assistants for every class they've assisted. For every three
    credits that an assistant has, the assistant is awarded a gift certifcate equal
    in value to the standard class cost at the assistant's campus, and debited three
    credits.

    Runs every midnight via cron job.
    """

    def run(self):
        previous_day = datetime.now().date() + timedelta(days=-1)
        logging.info("Starting assistant credit and GC award for {}".format(str(previous_day)))
        db.session.begin(subtransactions=True)

        assistants = Assistant.query_active()
        for assistant in assistants:
            classes_assisted = db.session.query(Schedule)\
                                         .filter(Schedule.assistants.any(id=assistant.id))\
                                         .filter(Schedule.date == previous_day)\
                                         .filter(or_(Schedule.deleted == False, Schedule.deleted == None))\
                                         .all()

            if classes_assisted:
                current_assistant_credits = assistant.credits
                assistant.credits += len(classes_assisted)
                logging.info("Adjusted {}'s (id: {}) credits from {} to {} based on classes assisted.".format(assistant.full_name,
                                                                                                              assistant.id,
                                                                                                              current_assistant_credits,
                                                                                                              assistant.credits))

            if assistant.credits >= 3:
                assistant_campus = assistant.campuses[0]
                gcs_to_award = assistant.credits / 3
                assistant.credits -= (gcs_to_award * 3)

                for x in range(gcs_to_award):
                    try:
                        new_gc = GiftCertificate(campus_id=assistant_campus.id,
                                                 delivery_method=1,
                                                 sender_name=assistant_campus.name,
                                                 sender_email=assistant_campus.email,
                                                 sender_phone=assistant_campus.phone,
                                                 amount_to_give=assistant_campus.base_cost,
                                                 recipient_name=assistant.full_name,
                                                 recipient_email=assistant.email,
                                                 message="You've been awarded a Gift Certifcate for your assistance!")
                        db.session.add(new_gc)
                        email_gift_certificate(new_gc)
                    except Exception as e:
                        logging.warning('Failed to create/send GC: {}'.format(str(e)))

                logging.info("Awarded {} (id: {}) {} gift certificate(s) and debited {} credits.".format(assistant.full_name,
                                                                                                         assistant.id,
                                                                                                         gcs_to_award,
                                                                                                         gcs_to_award * 3))

            db.session.add(assistant)

        db.session.commit()
