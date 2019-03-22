# encoding=utf-8
"""All static content needs to be editable

Revision ID: 585dc65df58c
Revises: 539f62056fe5
Create Date: 2016-02-08 16:05:46.043957

"""

# revision identifiers, used by Alembic.
revision = '585dc65df58c'
down_revision = '539f62056fe5'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


static_page = sa.sql.table(
    "static_page",
    sa.Column("path", sa.String(50), index=True, unique=True),
    sa.Column("title", sa.String(100)),
    sa.Column("body", sa.Text),
    sa.Column("category", sa.String(1)),
)

CATEGORY_CONTENT = "c"
CATEGORY_PAGE = "p"


def upgrade():
    op.execute("ALTER TABLE static_page CONVERT TO CHARACTER SET utf8mb4")
    op.execute(
        static_page.update()
        .where(static_page.c.category == CATEGORY_CONTENT)
        .values({"category": "p"})
    )
    db.session.begin()
    update = static_page.insert().values(path=sa.bindparam("path"), title=sa.bindparam("title"), body=sa.bindparam("body"), category=sa.bindparam("category"))
    db.session.execute(update, [{
        "path": "/terms/cancellation/body",
        "title": "Hipcooks: Class, Cancellation, Makeup Policy",
        "body": u"""
            <h2 class="JandaQuickNote-normal">CLASS POLICIES</h2>
            <p>All classes require advance registration and payment is made in full at the time of registration.</p>
            <h2>CANCELLATION AND MAKE-UP POLICY</h2>
            <p>You may cancel your class up to 48 hours before the class start-time to receive either class credit or a refund. If you choose a refund, a $5 per person processing fee will be removed.</p>
            <p>If it is past the 48-hour mark and you find that you cannot attend, the payment is non-refundable. You will still receive the class recipes but the class fee/option to reschedule will be forfeit. You can, however, send someone in your place to attend the class.</p>
            <p>If it is past the 48-hour mark and you need to cancel the reservation, please do so online. This will automatically notify our Wait List, and we make every effort to help. If someone off the wait list takes your place, we will send you class credit. Please note that this is not a guarantee. If it is past the 48-hour mark, expect that your payment is non-refundable.</p>
            <p>* Inclement Weather: if weather conditions are unsafe and travel is not advised in the greater Metro area, we will cancel the entire class. During days of inclement weather, we will notify the class of a cancellation via email at least 3 hours prior, so please check your email before travelling. Otherwise, the class will be held, and the cancellation policy above holds.</p>
        """,
        "category": CATEGORY_CONTENT,
    }, {
        "path": "/terms/gift-certificate/body",
        "title": "Hipcooks: Gift Certificate Policy",
        "body": u"""
            <h2 class="JandaQuickNote-normal">GIFT CERTIFICATE POLICY</h2>
            <p> Our Gift Certificates (and class make-up codes) can be applied to classes we offer at any Hipcooks location. The recipient simply signs up for any available class, provides the Gift Certificate number and "voilà" we're cooking! </p>
            <p> The certificates do not expire and are worth their value until used in full. </p>
            <p> Gift certificates are non-refundable. They are redeemable for class credit only, and are not exchangeable for cash or for items in our retail store. </p>
        """,
        "category": CATEGORY_CONTENT,
    }, {
        "path": "/terms/privacy/body",
        "title": "Hipcooks: Privacy Policy",
        "body": u"""
            <h2 class="JandaQuickNote-normal">Privacy Policy for Hipcooks</h2>

            <h3 class="JandaQuickNote-normal">Introduction</h3>
            <p>This Privacy Policy governs the manner in which Hipcooks collects, uses, maintains and discloses information collected from users (each, a “User”) of the http://www.hipcooks.com website (“Site”). This privacy policy applies to the Site and all products and services offered by Hipcooks.</p>

            <p>This agreement last updated February 1, 2016.</p>

            <h3 class="JandaQuickNote-normal">Personal identification information</h3>
            <p>We may collect personal identification information from Users in a variety of ways, including, but not limited to, when Users visit our site, place an order, fill out a form, and in connection with other activities, services, features or resources we make available on our Site. Users may be asked for, as appropriate, name, email address, mailing address, phone number. Users may, however, visit our Site anonymously. We will collect personal identification information from Users only if they voluntarily submit such information to us. Users can always refuse to supply personally identification information, except that it may prevent them from engaging in certain Site related activities.</p>

            <h3 class="JandaQuickNote-normal">Non-personal identification information</h3>
            <p>We may collect non-personal identification information about Users whenever they interact with our Site. Non-personal identification information may include the browser name, the type of computer and technical information about Users means of connection to our Site, such as the operating system and the Internet service providers utilized and other similar information.</p>

            <h3 class="JandaQuickNote-normal">Web browser cookies</h3>
            <p>Our Site may use “cookies” to enhance User experience. User’s web browser places cookies on their hard drive for record-keeping purposes and sometimes to track information about them. User may choose to set their web browser to refuse cookies, or to alert you when cookies are being sent. If they do so, note that some parts of the Site may not function properly.</p>

            <h3 class="JandaQuickNote-normal">How we use collected information</h3>
            <p>
                Hipcooks may collect and use Users personal information for the following purposes:
                <ul>
                    <li>To improve customer service – Information you provide helps us respond to your customer service requests and support needs more efficiently.</li>
                    <li>To process payments – We may use the information Users provide about themselves when placing an order only to provide service to that order. We do not share this information with outside parties except to the extent necessary to provide the service.</li>
                    <li>To send periodic emails – We may use the email address to send User information and updates pertaining to their order. It may also be used to respond to their inquiries, questions, and/or other requests. If User decides to opt-in to our mailing list, they will receive emails that may include company news, updates, related product or service information, etc. If at any time the User would like to unsubscribe from receiving future emails, we include detailed unsubscribe instructions at the bottom of each email.</li>
                </ul>
            </p>
            <h3 class="JandaQuickNote-normal">How we protect your information</h3>
            <p>We adopt appropriate data collection, storage and processing practices and security measures to protect against unauthorized access, alteration, disclosure or destruction of your personal information, username, password, transaction information and data stored on our Site.</p>

            <h3 class="JandaQuickNote-normal">Sharing your personal information</h3>
            <p>We do not sell, trade, or rent Users personal identification information to others. We may share generic aggregated demographic information not linked to any personal identification information regarding visitors and users with our business partners, trusted affiliates and advertisers for the purposes outlined above. We may use third party service providers to help us operate our business and the Site or administer activities on our behalf, such as sending out newsletters or surveys. We may share your information with these third parties for those limited purposes provided that you have given us your permission.</p>

            <h3 class="JandaQuickNote-normal">Third party websites</h3>
            <p>Users may find content on our Site that link to the sites and services of our partners, suppliers, advertisers, sponsors, licensors and other third parties. We do not control the content or links that appear on these sites and are not responsible for the practices employed by websites linked to or from our Site. In addition, these sites or services, including their content and links, may be constantly changing. These sites and services may have their own privacy policies and customer service policies. Browsing and interaction on any other website, including websites which have a link to our Site, is subject to that website’s own terms and policies.</p>

            <h3 class="JandaQuickNote-normal">Changes to this privacy policy</h3>
            <p>Hipcooks has the discretion to update this privacy policy at any time. When we do, we will revise the updated date at the top of this page. We encourage Users to frequently check this page for any changes to stay informed about how we are helping to protect the personal information we collect. You acknowledge and agree that it is your responsibility to review this privacy policy periodically and become aware of modifications.</p>

            <h3 class="JandaQuickNote-normal">Your acceptance of these terms</h3>
            <p>By using this Site, you signify your acceptance of this policy and terms ofservice. If you do not agree to this policy, please do not use our Site. Your continued use of the Site following the posting of changes to this policy will be deemed your acceptance of those changes.</p>

            <h3 class="JandaQuickNote-normal">Contact Information</h3>
            <p>If you have any questions about this Privacy Policy, the practices of this site, or your dealings with this site, please contact us at:
                <br>
                Hipcooks <br>
                642 Moulton Ave <br>
                Unit E21 <br>
                LA CA 90031
            </p>
        """,
        "category": CATEGORY_CONTENT,
    }, {
        "path": "/terms/service/body",
        "title": "Hipcooks: Terms of service",
        "body": u"""
            <h2 class="JandaQuickNote-normal">Terms of Service for Hipcooks</h2>

            <h3 class="JandaQuickNote-normal">Introduction</h3>
            <p>Welcome! This website is owned by Hipcooks, Inc. and licensed by Hip Unlimited, LLC. By visiting our website and accessing the information, resources, services, products, and tools we provide, you understand and agree to accept and adhere to the following terms and conditions as stated in this policy (hereafter referred to as ‘User Agreement’), along with the terms and conditions as stated in our Privacy Policy (please refer to the Privacy Policy section for more information).</p>

            <p>This agreement last updated February 1, 2016.</p>

            <p>We reserve the right to change this User Agreement from time to time without notice. You acknowledge and agree that it is your responsibility to review this User Agreement periodically to familiarize yourself with any modifications. Your continued use of this site after such modifications will constitute acknowledgment and agreement of the modified terms and conditions.</p>

            <h3 class="JandaQuickNote-normal">Responsible Use and Conduct</h3>
            <p>
                By visiting our website and accessing the information, resources, services, products, and tools we provide for you, either directly or indirectly (hereafter referred to as ‘Resources’), you agree to use these Resources only for the purposes intended as permitted by (a) the terms of this User Agreement, and (b) applicable laws, regulations and generally accepted online practices or guidelines.
                Wherein, you understand that:
                <ol type="a">
                    <li>In order to access our Resources, you may be required to provide certain information about yourself (such as identification, contact details, etc.) as part of the registration process, or as part of your ability to use the Resources. You agree that any information you provide will always be accurate, correct, and up to date.</li>
                    <li>You are responsible for maintaining the confidentiality of any login information associated with any account you use to access our Resources. Accordingly, you are responsible for all activities that occur under your account/s.</li>
                    <li>Accessing (or attempting to access) any of our Resources by any means other than through the means we provide, is strictly prohibited. You specifically agree not to access (or attempt to access) any of our Resources through any automated, unethical or unconventional means.</li>
                    <li>Engaging in any activity that disrupts or interferes with our Resources, including the servers and/or networks to which our Resources are located or connected, is strictly prohibited.</li>
                    <li>Attempting to copy, duplicate, reproduce, sell, trade, or resell our Resources is strictly prohibited.</li>
                    <li>You are solely responsible any consequences, losses, or damages that we may directly or indirectly incur or suffer due to any unauthorized activities conducted by you, as explained above, and may incur criminal or civil liability.</li>
                    <li>We may provide various open communication tools on our website, such as blog comments, blog posts, public chat, forums, message boards, newsgroups, product ratings and reviews, various social media services, etc. You understand that generally we do not pre-screen or monitor the content posted by users of these various communication tools, which means that if you choose to use these tools to submit any type of content to our website, then it is your personal responsibility to use these tools in a responsible and ethical manner. By posting information or otherwise using any open communication tools as mentioned, you agree that you will not upload, post, share, or otherwise distribute any content that:</li>
                        <ol type="i">
                            <li>Is illegal, threatening, defamatory, abusive, harassing, degrading, intimidating, fraudulent, deceptive, invasive, racist, or contains any type of suggestive, inappropriate, or explicit language;<br>
                            Infringes on any trademark, patent, trade secret, copyright, or other proprietary right of any party;</li>
                            <li>Contains any type of unauthorized or unsolicited advertising;</li>
                            <li>Impersonates any person or entity, including any Hipcooks employees or representatives.</li>
                        </ol>
                    We have the right at our sole discretion to remove any content that, we feel in our judgment does not comply with this User Agreement, along with any content that we feel is otherwise offensive, harmful, objectionable, inaccurate, or violates any 3rd party copyrights or trademarks. We are not responsible for any delay or failure in removing such content. If you post content that we choose to remove, you hereby consent to such removal, and consent to waive any claim against us.
                    <li>We do not assume any liability for any content posted by you or any other 3rd party users of our website. However, any content posted by you using any open communication tools on our website, provided that it doesn’t violate or infringe on any 3rd party copyrights or trademarks, becomes the property of Hipcooks, and as such, gives us a perpetual, irrevocable, worldwide, royalty-free, exclusive license to reproduce, modify, adapt, translate, publish, publicly display and/or distribute as we see fit. This only refers and applies to content posted via open communication tools as described, and does not refer to information that is provided as part of the registration process, necessary in order to use our Resources. All information provided as part of our registration process is covered by our privacy policy.</li>
                    <li>You agree to indemnify and hold harmless Hipcooks and its parent company and affiliates, and their directors, officers, managers, employees, donors, agents, and licensors, from and against all losses, expenses, damages and costs, including reasonable attorneys’ fees, resulting from any violation of this User Agreement or the failure to fulfill any obligations relating to your account incurred by you or any other person using your account. We reserve the right to take over the exclusive defense of any claim for which we are entitled to indemnification under this User Agreement. In such event, you shall provide us with such cooperation as is reasonably requested by us.</li>
                </ol>
            </p>

            <h3 class="JandaQuickNote-normal">Privacy</h3>
            <p>Your privacy is very important to us, which is why we’ve created a separate Privacy Policy in order to explain in detail how we collect, manage, process, secure, and store your private information. Our privacy policy is included under the scope of this User Agreement. To read our privacy policy in its entirety, click here.</p>

            <h3 class="JandaQuickNote-normal">Limitation of Warranties</h3>
            <p>By using our website, you understand and agree that all Resources we provide are “as is” and “as available”. This means that we do not represent or warrant to you that:
            <ol type="i">
                <li>the use of our Resources will meet your needs or requirements.</li>
                <li>the use of our Resources will be uninterrupted, timely, secure or free from errors.</li>
                <li>the information obtained by using our Resources will be accurate or reliable, and</li>
                <li>any defects in the operation or functionality of any Resources we provide will be repaired or corrected.</li>
                Furthermore, you understand and agree that:
                <li>any content downloaded or otherwise obtained through the use of our Resources is done at your own discretion and risk, and that you are solely responsible for any damage to your computer or other devices for any loss of data that may result from the download of such content.</li>
                <li>no information or advice, whether expressed, implied, oral or written, obtained by you from Hipcooks or through any Resources we provide shall create any warranty, guarantee, or conditions of any kind, except for those expressly outlined in this User Agreement.</li>
            </ol>

            <h3 class="JandaQuickNote-normal">Limitation of Liability</h3>
            <p>In conjunction with the Limitation of Warranties as explained above, you expressly understand and agree that any claim against us shall be limited to the amount you paid, if any, for use of products and/or services. Hipcooks will not be liable for any direct, indirect, incidental, consequential or exemplary loss or damages which may be incurred by you as a result of using our Resources, or as a result of any changes, data loss or corruption, cancellation, loss of access, or downtime to the full extent that applicable limitation of liability laws apply.</p>

            <h3 class="JandaQuickNote-normal">Copyrights/Trademarks</h3>
            <p>All content and materials available on Hipcooks, including but not limited to text, graphics, website name, code, images and logos are the intellectual property of Hicpooks, Inc., and are protected by applicable copyright and trademark law. Any inappropriate use, including but not limited to the reproduction, distribution, display or transmission of any content on this site is strictly prohibited, unless specifically authorized by Hipcooks.</p>

            <h3 class="JandaQuickNote-normal">Termination of Use</h3>
            <p>You agree that we may, at our sole discretion, suspend or terminate your access to all or part of our website and Resources with or without notice and for any reason, including, without limitation, breach of this User Agreement. Any suspected illegal, fraudulent or abusive activity may be grounds for terminating your relationship and may be referred to appropriate law enforcement authorities. Upon suspension or termination, your right to use the Resources we provide will immediately cease, and we reserve the right to remove or delete any information that you may have on file with us, including any account or login information.</p>

            <h3 class="JandaQuickNote-normal">Governing Law</h3>
            <p>This website is controlled by Hipcooks from our offices located in the state of CA, US. It can be accessed by most countries around the world. As each country has laws that may differ from those of CA, by accessing our website, you agree that the statutes and laws of CA, without regard to the conflict of laws and the United Nations Convention on the International Sales of Goods, will apply to all matters relating to the use of this website and the purchase of any products or services through this site.</p>
            <p>Furthermore, any action to enforce this User Agreement shall be brought in the federal or state courts located in US, CA You hereby agree to personal jurisdiction by such courts, and waive any jurisdictional, venue, or inconvenient forum objections to such courts.</p>

            <h3 class="JandaQuickNote-normal">Guarantee</h3>
            <p>UNLESS OTHERWISE EXPRESSED, HIPCOOKS EXPRESSLY DISCLAIMS ALL WARRANTIES AND CONDITIONS OF ANY KIND, WHETHER EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO THE IMPLIED WARRANTIES AND CONDITIONS OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.</p>

            <h3 class="JandaQuickNote-normal">Contact Information</h3>
            <p>If you have any questions or comments about these our Terms of Service as outlined above, you can contact us at:</p>
            Hipcooks <br>
            642 Moulton Ave <br>
            Unit E21 <br>
            LA CA 90031</h3>
        """,
        "category": CATEGORY_CONTENT,
    }])
    db.session.commit()


def downgrade():
    op.execute(static_page.delete()
               .where(static_page.c.path.like("/terms/%/body")))
