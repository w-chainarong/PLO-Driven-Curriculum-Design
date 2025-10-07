from django import template

register = template.Library()

# 🔢 ดึงค่าจาก list ตาม index
@register.filter
def index(sequence, position):
    try:
        position = int(position)
        return sequence[position - 1]
    except (IndexError, ValueError, TypeError):
        return ''

# 🔠 แยก string ด้วยตัวแบ่ง เช่น comma
@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)

# 🔁 สร้าง range 1 ถึง value
@register.filter(name='to_range')
def to_range(value):
    try:
        value = int(value)
        return range(1, value + 1)
    except (ValueError, TypeError):
        return range(0)

# 🔍 ดึงค่าใน dictionary ตาม key
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

# ➕ บวกค่าทั้งหมดใน list
@register.filter(name='sum_list')
def sum_list(value):
    try:
        return sum(value)
    except TypeError:
        return 0

# ➗ แบ่งค่า (ระวังหาร 0)
@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, ZeroDivisionError):
        return 0

# 📌 ดึง attribute ตามชื่อ เช่น course|map:'credits'
@register.filter
def map(value, attr_name):
    try:
        return [getattr(obj, attr_name, 0) for obj in value]
    except:
        return []

# 🆕 ดึงค่า K/S/E/C จาก course ตาม type letter
@register.filter
def get_ksec_value(course, type_letter):
    try:
        if type_letter == 'K':
            return course.knowledge
        elif type_letter == 'S':
            return course.skills
        elif type_letter == 'E':
            return course.ethics
        elif type_letter == 'C':
            return course.character
        return ''
    except:
        return ''
