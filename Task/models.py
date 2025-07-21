from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Note(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, null=True,blank=True)
    title= models.CharField(max_length=200)
    description = models.TextField(null=True,blank=True)
    complete = models.BooleanField(default=False) #when item first created it is not complete
    create = models.DateTimeField(auto_now_add=True)
    tags        = models.ManyToManyField(Tag, blank=True, related_name='notes')
    image = models.ImageField(upload_to='note_images/', blank=True, null=True)
   # tags=models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, blank=True) #esto es lo mismo
    
    history = HistoricalRecords()

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['complete']



# ─────────────────────────────── main model ──────────────────────────────

class Task(models.Model):
    """
    A schedulable (optionally recurring) task belonging to a user.
    Can span a date/time range and have priority & recurrence metadata.
    """
    # Basic
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)

    # Date / time window
    start_date = models.DateField(
        null=True, blank=True,
        help_text="Start date (was previously due_date)."
    )
    end_date = models.DateField(
        null=True, blank=True,
        help_text="End date (must be on or after start date)."
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time   = models.TimeField(null=True, blank=True)

    # Priority
    PRIORITY_LOW = "L"
    PRIORITY_MED = "M"
    PRIORITY_HIGH = "H"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MED, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]
    priority = models.CharField(
        max_length=1,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MED
    )

    # Recurrence (kept generic for now)
    repeat = models.CharField(
        max_length=20, null=True, blank=True,
        help_text="e.g. daily, weekly, custom, etc."
    )
    timezone = models.CharField(max_length=50, null=True, blank=True)
    custom_days = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Comma-separated day codes if using a custom pattern (e.g. MON,WED,FRI)."
    )
    repeat_until = models.DateField(null=True, blank=True)
    repeat_forever = models.BooleanField(default=False)

    # Extra info
    notes = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')

    color = models.CharField(
        max_length=20,
        default="blue",
        help_text="Colour used in calendar or list view."
    )

    completed = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ('-date_created',)

    def __str__(self):
        return f"{self.title} ({'Done' if self.completed else 'Pending'})"

    # --- Validation ---
    def clean(self):
        from django.core.exceptions import ValidationError
        # Date logic
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
        # Time logic (only if both times and same day range)
        if (self.start_time and self.end_time and
            self.start_date == self.end_date and
            self.end_time < self.start_time):
            raise ValidationError("End time cannot be before start time when start/end date are equal.")
        # Recurrence safety
        if self.repeat and not (self.repeat_forever or self.repeat_until):
            # Not mandatory, but a gentle constraint if you want
            pass

    # Convenience
    @property
    def is_recurring(self):
        return bool(self.repeat)

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 1 if self.start_date else None
