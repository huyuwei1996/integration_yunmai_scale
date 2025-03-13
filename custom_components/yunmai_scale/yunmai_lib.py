"""
Based on YunmaiLib.py

Copyright (C) 2021 Paxy
Copyright (C) 2018 olie.xdev <olie.xdev@googlemail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import math


class YmLib:

    def __init__(self, sex: int, height: float, active: bool):
        """_summary_

        :param sex: male = 1; female = 0
        :param height: cm
        :param active:
        """
        self.sex = sex
        self.height = height
        self.fitness_body_type = active

    def get_water(self, body_fat) -> float:
        return ((100.0 - body_fat) * 0.726 * 100.0 + 0.5) / 100.0

    def get_bmi(self, weight) -> float:
        return weight / ((self.height / 100.0) ** 2)

    def get_fat(self, age, weight, resistance) -> float:
        #  for < 0x1e version devices
        r = (resistance - 100.0) / 100.0
        h = self.height / 100.0
        if r >= 1:
            r = math.sqrt(r)
        fat = (weight * 1.5 / h / h) + (age * 0.08)
        if self.sex == 1:
            fat -= 10.8
        fat = (fat - 7.4) + r
        if fat < 5.0 or fat > 75.0:
            fat = 0.0
        return fat

    def get_muscle(self, body_fat) -> float:
        muscle = (100.0 - body_fat) * 0.67
        if self.fitness_body_type:
            muscle = (100.0 - body_fat) * 0.7
        return ((muscle * 100.0) + 0.5) / 100.0

    def get_skeletal_muscle(self, body_fat) -> float:
        muscle = (100.0 - body_fat) * 0.53
        if self.fitness_body_type:
            muscle = (100.0 - body_fat) * 0.6
        return ((muscle * 100.0) + 0.5) / 100.0

    def get_bone_mass(self, muscle, weight) -> float:
        h = self.height - 170.0
        if self.sex:
            bone_mass = ((weight * (muscle / 100.0) * 4.0) / 7.0 * 0.22 * 0.6) + (
                h / 100.0
            )
        else:
            bone_mass = ((weight * (muscle / 100.0) * 4.0) / 7.0 * 0.34 * 0.45) + (
                h / 100.0
            )
        return ((bone_mass * 10.0) + 0.5) / 10.0

    def get_lean_body_mass(self, weight, body_fat) -> float:
        return weight * (100.0 - body_fat) / 100.0

    def get_visceral_fat(self, body_fat, age) -> float:
        f = body_fat
        a = min(max(age, 18), 120)

        if not self.fitness_body_type:
            # Determine fat adjustment based on sex and age
            if self.sex:  # male
                fat_adjustment = 21.0 if a < 40 else (22.0 if a < 60 else 24.0)
            else:  # female
                fat_adjustment = 34.0 if a < 40 else (35.0 if a < 60 else 36.0)

            f -= fat_adjustment
            d = 1.1 if f > 0.0 else 1.0  # Default value for d if not explicitly set
            vf = (f / d) + 9.5

        else:
            # Fitness body type calculation
            vf = (
                ((body_fat - 15.0) / 1.1 + 12.0)
                if body_fat > 15.0
                else (-1 * (15.0 - body_fat) / 1.4 + 12.0)
            )

        # Clamp the result within valid range
        return max(1.0, min(30.0 if not self.fitness_body_type else 9.0, vf))
