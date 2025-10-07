from django.db import models


class Curriculum(models.Model):
    name = models.CharField(max_length=255)
    password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Password required to unlock the edit mode of the main credit table."
    )
    clo_edit_password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Password required to unlock the CLO–KSEC Mapping interface."
    )

    def __str__(self):
        return self.name


class CreditRow(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)

    ROW_TYPES = [
        ('general', 'General Education'),
        ('core', 'Core Education'),
        ('free', 'Free Elective'),
        ('plo', 'PLO-based Category'),
    ]

    name = models.CharField(max_length=200)
    row_type = models.CharField(max_length=10, choices=ROW_TYPES)
    credits_sem1 = models.IntegerField(default=0)
    credits_sem2 = models.IntegerField(default=0)
    credits_sem3 = models.IntegerField(default=0)
    credits_sem4 = models.IntegerField(default=0)
    credits_sem5 = models.IntegerField(default=0)
    credits_sem6 = models.IntegerField(default=0)
    credits_sem7 = models.IntegerField(default=0)
    credits_sem8 = models.IntegerField(default=0)

    def credit_list(self):
        """Return a list of credits for semesters 1–8."""
        return [
            self.credits_sem1, self.credits_sem2, self.credits_sem3, self.credits_sem4,
            self.credits_sem5, self.credits_sem6, self.credits_sem7, self.credits_sem8
        ]

    def total_credits(self):
        """Return the total number of credits across all semesters."""
        return sum(self.credit_list())

    def __str__(self):
        return f"{self.name} [{self.row_type}]"


class Course(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    credit_row = models.ForeignKey(
        CreditRow, on_delete=models.CASCADE, related_name='courses', null=True, blank=True
    )
    category = models.CharField(max_length=50, blank=True, null=True)
    semester = models.PositiveSmallIntegerField(
        choices=[(i + 1, f'Year {i // 2 + 1}/{i % 2 + 1}') for i in range(8)]
    )
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=255)
    credits = models.IntegerField()
    plo = models.CharField(max_length=10)
    description = models.TextField(blank=True, null=True)

    knowledge = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    ethics = models.TextField(blank=True, null=True)
    character = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.course_code} - {self.course_name}'


class YLOPerPLOSemester(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    plo = models.CharField(max_length=50)
    semester = models.PositiveSmallIntegerField()
    summary_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"YLO Summary for {self.plo} - Semester {self.semester}"


class KSECItem(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    semester = models.IntegerField(default=0)
    type = models.CharField(
        max_length=1,
        choices=[
            ('K', 'Knowledge'),
            ('S', 'Skills'),
            ('E', 'Ethics'),
            ('C', 'Character'),
        ]
    )
    category_type = models.CharField(
        max_length=2,
        choices=[
            ('GE', 'General Education'),
            ('CE', 'Core Education')
        ]
    )
    description = models.TextField()
    sort_order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.category_type}({self.type}){self.sort_order + 1}"


class CLO(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    index = models.PositiveIntegerField()
    clo = models.TextField()
    bloom = models.CharField(max_length=50, blank=True, null=True)
    k = models.CharField(max_length=20, blank=True, null=True)
    s = models.CharField(max_length=20, blank=True, null=True)
    e = models.CharField(max_length=20, blank=True, null=True)
    c = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'table_clo'
        ordering = ['index']

    def __str__(self):
        return f"{self.course.course_code} - CLO{self.index}"


class CLOSummary(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    bloom_score = models.IntegerField(default=0)
    k_percent = models.FloatField(default=0.0)
    s_percent = models.FloatField(default=0.0)
    e_percent = models.FloatField(default=0.0)
    c_percent = models.FloatField(default=0.0)

    class Meta:
        db_table = 'table_clo_summary'

    def __str__(self):
        return f"Summary for {self.course.course_code}"
