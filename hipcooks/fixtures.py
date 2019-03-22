from fixture import DataSet
from datetime import datetime, date, time


class UserData(DataSet):
    class LoggedInUser:
        id = 101
        username = "test_public"
        first_name = "TestPublic"
        last_name = "Public",
        email = "test.public@parthenonsoftware.com"
        raw_password = "password"
        password = "sha1$028a$a28e49a9055dc9b5eb7f75d2cebeacec2f8d5634"
        is_active = True
        is_superuser = False

    class AssistantUser(LoggedInUser):
        id = 102
        username = "assistant"
        first_name = "Assistant"
        last_name = "Assistant"
        email = "assistant@parthenonsoftware.com"

    class TeacherUser:
        id = 103
        username = "teacher"
        first_name = "Teacher"
        last_name = "Teacher"
        email = "teacher@parthenonsoftware.com"
        raw_password = "password"
        password = "sha1$028a$a28e49a9055dc9b5eb7f75d2cebeacec2f8d5634"
        is_active = True
        is_superuser = False

    class OtherUser(LoggedInUser):
        id = 104
        username = "other_user"
        first_name = "Other"
        last_name = "User"
        email = "other.user@parthenonsoftware.com"

    class InactiveAssistantUser(LoggedInUser):
        id = 105
        username = "inactive"
        first_name = "Inactive"
        last_name = "Assistant"
        email = "inactive.assistant@parthenonsoftware.com"

    class MultiCampusTeacherUser(TeacherUser):
        id = 106
        username = "multicampusteacher"
        first_name = "Campuses"
        email = "mct@parthenonsoftware.com"


class CampusData(DataSet):
    class TestCampus:
        id = 111
        domain = "test"
        name = "Test Place"
        start_time = "15:00"
        duration = 3

    class OtherCampus:
        id = 112
        domain = "other"
        name = "Other Place"
        start_time = "13:00"
        duration = 2


class AssistantData(DataSet):
    class Assistant:
        id = 121
        user = UserData.AssistantUser
        first_name = UserData.AssistantUser.first_name
        last_name = UserData.AssistantUser.last_name
        active = True
        email = UserData.AssistantUser.email
        mobile_phone = ""

    class InactiveAssistant:
        id = 122
        user = UserData.InactiveAssistantUser
        first_name = UserData.InactiveAssistantUser.first_name
        last_name = UserData.InactiveAssistantUser.last_name
        active = False
        email = UserData.InactiveAssistantUser.email
        mobile_phone = ""


class TeacherData(DataSet):
    class Teacher:
        id = 131
        user = UserData.TeacherUser
        campuses = [CampusData.TestCampus]
        bio = "I'm a teacher"
        pic = None
        mobile_phone = ""
        home_phone = ""
        work_phone = ""
        street = "1 Road Dr."
        city = "City"
        state = "St"
        zip_code = 12345
        ssn = "1112223333"

    class MultiCampusTeacher(Teacher):
        id = 132
        user = UserData.MultiCampusTeacherUser
        campuses = [CampusData.TestCampus, CampusData.OtherCampus]
        bio = "I'm a teacher that travels a lot"


class ClassData(DataSet):
    class TestClass:
        id = 141
        order = 50
        title = "Test Class"
        abbr = "TC101"
        description = "Take a Test Class"
        menu = "Make food"
        knife_level = "3"
        veggie_level = "1"
        dairy_level = "0"
        wheat_level = "2"
        cost_override = None

    class OldClass(TestClass):
        id = 142
        title = "Old Class"
        abbr = "TC100"
        description = "A now obsolete test class"
        menu = "Eat like a Pharoah"
        cost_override = 100

    class PrivateClass(TestClass):
        id = 143
        title = "Private Class"
        abbr = "PTC"
        description = "A test class for the people who prefer privacy"
        menu = "Can't tell you, it's a secret"


class RecipeSetData(DataSet):
    class TestClassRecipeSet:
        cls = ClassData.TestClass
        intro = "Recipes!"
        last_updated = datetime(2015, 1, 1)


class RecipeData(DataSet):
    class TestClassRecipe:
        id = 191
        set = RecipeSetData.TestClassRecipeSet
        title = "Food"
        serves = "10-20"
        ingredients = "Food"
        instructions = "Actions"
        order = 0


class ScheduleData(DataSet):
    class TestClassSchedule:
        id = 151
        campus = CampusData.TestCampus
        cls = ClassData.TestClass
        is_public = True
        date = date(2100, 12, 31)
        time = time(12, 0, 0)
        assistants = [AssistantData.Assistant]
        teachers = [TeacherData.Teacher]
        duration = 1.5
        spaces = 99
        comments = ""

    class TestClassOldSchedule(TestClassSchedule):
        id = 152
        date = date(2000, 1, 1)
        cls = ClassData.OldClass

    class TestClassFullSchedule(TestClassSchedule):
        id = 153
        date = date(2050, 6, 15)
        spaces = 0

    class TestClassPrivateSchedule(TestClassSchedule):
        id = 154
        date = date(2025, 2, 4)
        cls = ClassData.PrivateClass
        is_public = False


class PurchaseData(DataSet):
    class Purchase:
        id = 201
        timestamp = datetime(1999, 1, 1)
        ip_address = "127.0.0.1"
        amount = 100
        first_name = UserData.LoggedInUser.first_name
        last_name = UserData.LoggedInUser.last_name
        email = UserData.LoggedInUser.email
        phone = None
        authorization_code = "AUTH--"


class ScheduleOrderData(DataSet):
    class Order:
        id = 161
        schedule = ScheduleData.TestClassSchedule
        user = UserData.LoggedInUser
        purchase = PurchaseData.Purchase
        comments = ""
        unit_price = 100
        cancelled = False

    class UnpaidOrder:
        id = 162
        schedule = ScheduleData.TestClassSchedule
        user = UserData.LoggedInUser
        purchase = None
        comments = ""
        unit_price = 65
        cancelled = False


class GuestOrderData(DataSet):
    class Guest:
        id = 171
        order = ScheduleOrderData.Order
        cancelled = False

    class UnpaidGuest:
        id = 172
        order = ScheduleOrderData.UnpaidOrder
        cancelled = False


class GiftCertificateData(DataSet):
    class Gift:
        id = 171
        campus = CampusData.TestCampus
        created = datetime(2015, 1, 1)
        sender_name = UserData.LoggedInUser.first_name
        sender_email = UserData.LoggedInUser.last_name
        amount_to_give = 65
        recipient_name = "Recipient"
        message = "A test gift certificate"
        giftcard = True
        code = "giftcode--"

    class SecondGift(Gift):
        id = 172
        message = ("Another test gift certificate. "
                   "So two schedules can be purchased")
        code = "giftcode2-"


class StaticPageData(DataSet):
    class Page:
        id = 181
        path = "test-page"
        title = "Static Page"
        body = "This is a test page"
        category = "c"
