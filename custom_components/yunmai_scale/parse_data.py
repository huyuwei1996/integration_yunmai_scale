"""Parse data from Yunmai scale advertisements."""

from .yunmai_lib import YmLib


def process_data(
    data: str, age: int = 25, sex: int = 1, height: float = 170, is_active: bool = False
) -> dict:
    """
    Process the raw advertisement data from Yunmai scale.

    :param data: Hexadecimal string of advertisement data
    :param age: User age
    :param sex: User gender (1 for male, 0 for female)
    :param height: User height in cm
    :param is_active: Whether the user has an active lifestyle
    :return: Dictionary with processed scale measurements
    """
    if not data or len(data) < 26:
        return {}

    mac_suffix = data[:8]
    identifier = data[8:14]
    count = int(data[14:16], 16)
    credibility = data[16:18]  # 可信度 3为最稳定读数、00为称重结束
    weight = int(data[18:22], 16) * 0.01  # 精确到0.01公斤（10克） 单位kg
    resistance = int((data[22:26]), 16)  # 阻抗值应<3000（0x0BB8）

    # If status is not reliable, only return weight data
    if credibility == '00':
        return {'status': 'idle'}

    if credibility and credibility != '03':
        return {
            'weight': weight,
            'count': count,
            'status': 'measuring',
        }

    # For stable measurements, calculate all metrics
    scale = YmLib(sex, height, is_active)
    bmi = scale.get_bmi(weight)
    fat = scale.get_fat(age, weight, resistance)
    muscle = scale.get_muscle(fat)
    water = scale.get_water(fat)
    bone_mass = scale.get_bone_mass(muscle, weight)
    skeletal_muscle = scale.get_skeletal_muscle(fat)
    lean_body_mass = scale.get_lean_body_mass(weight, fat)
    visceral_fat = scale.get_visceral_fat(fat, age)

    return {
        'weight': weight,
        'bmi': round(bmi, 1),
        'body_fat': round(fat, 1),
        'muscle_mass': round(muscle, 1),
        'water_percentage': round(water, 1),
        'bone_mass': round(bone_mass, 1),
        'skeletal_muscle': round(skeletal_muscle, 1),
        'lean_body_mass': round(lean_body_mass, 1),
        'visceral_fat': round(visceral_fat),
        'status': 'stable',
        'count': count,
    }
