# 定义一个游戏角色类（这是所有职业的爸爸/基类）
class Character:
    # 初始化方法：创建角色时自动调用
    # name: 角色名字，hp: 生命值，attack: 攻击力
    def __init__(self, name, hp, attack):
        self.name = name
        self.hp=hp
        self.attack=attack
        self.level=1  # 默认等级为1
    # 攻击方法：自己攻击目标
    # target: 要攻击的目标（另一个角色对象）
    def attack_target(self, target):
        damage = self.attack
        print(f"{self.name} attacks {target.name} for {damage} damage.")
        # 让目标调用自己的take_damage方法，承受伤害
        target.take_damage(damage)
    # 承受伤害方法：自己被攻击时调用
    # damage: 受到的伤害值
    def take_damage(self, damage):
        self.hp -= damage   # 生命值减去伤害
        print(f"{self.name} has {self.hp} HP left")# 显示剩余血量
         # 如果血量小于等于0，角色死亡
        if self.hp <= 0:
            print(f"{self.name} is dead!")
    # 显示状态方法：打印角色的所有属性
    def show_status(self):
        print(f"\n{self.name}(Level {self.level}): HP: {self.hp}, ATK= {self.attack}")
        print("=== 测试Character类 ===")
class Warrior(Character):
    def __init__(self, name):
        super().__init__(name, hp=150, attack=30)  # 战士有较高的生命值和攻击力
    # 战士独有属性：护甲（可以减免伤害）
        self.armor = 20

    def taunt(self, target):
        # 嘲讽行为：提示并“引导”敌人攻击自己（这里只是演示打印）
        print(f"{self.name} taunts {target.name}! {target.name} is provoked to attack {self.name}.")

    def take_damage(self, damage):
        # 计算实际伤害，减去护甲值
        actual_damage = max(1, damage - self.armor)  # 确保伤害至少为1
        print(f"{self.name}'s armor reduces damage from {damage} to {actual_damage}.")
        # 调用父类的 take_damage 处理生命值减少和死亡逻辑
        super().take_damage(actual_damage)
# warrior_test = Warrior("Conan")  # 创建战士，名字叫Conan
# warrior_test.show_status()        # 显示状态（继承自父类）
# print(f"战士额外属性 - 护甲: {warrior_test.armor}")  # 显示护甲值

# # 测试战士承受伤害（有护甲减免）
# warrior_test.take_damage(50)  # 受到50点伤害，应该被护甲减免
# enemy = Character("Enemy", 100, 10)  # 创建个敌人
# warrior_test.taunt(enemy)  # 战士嘲讽敌人
# 定义法师类，继承自Character
class Mage(Character):  # 括号里的Character表示继承
    # 初始化方法：创建法师时调用
    def __init__(self, name):
        # 调用父类Character的初始化方法
        # 法师：血量100，攻击力25（比战士血少，攻击也低）
        super().__init__(name, hp=100, attack=25)
        # 法师独有属性：魔法值（施法需要消耗）
        self.mana = 100
    
    # 法师独有技能：火球术（消耗魔法，造成高额伤害）
    def fireball(self, target):
        # 检查魔法值是否足够（需要30点魔法）
        if self.mana >= 30:
            damage = 50  # 火球术伤害50点
            self.mana -= 30  # 消耗30点魔法
            print(f"{self.name} casts Fireball for {damage} damage!")
            target.take_damage(damage)  # 目标承受伤害
            print(f"{self.name} has {self.mana} mana left")
        else:
            # 魔法不够，施法失败
            print(f"{self.name} has no mana!")
    
    # 重写父类的show_status方法（增加显示魔法值）
    def show_status(self):
        # 先调用父类的show_status，显示名字、等级、血量、攻击力
        super().show_status()
        # 再额外显示法师的魔法值
        print(f"   Mana: {self.mana}")
# 定义牧师类，继承自Character
class Priest(Character):  # 括号里的Character表示继承
    # 初始化方法：创建牧师时调用
    def __init__(self, name):
        # 调用父类Character的初始化方法
        # 牧师：血量120，攻击力15（血比法师多，但攻击最低）
        super().__init__(name, hp=120, attack=15)
        # 牧师独有属性：魔法值（治疗需要消耗）
        self.mana = 80
    
    # 牧师独有技能：治疗术（消耗魔法，恢复队友血量）
    def heal(self, target):
        # 检查魔法值是否足够（需要20点魔法）
        if self.mana >= 20:
            heal_amount = 40  # 治疗量40点
            target.hp += heal_amount  # 目标血量增加
            self.mana -= 20  # 消耗20点魔法
            print(f"{self.name} heals {target.name} for {heal_amount} HP!")
            print(f"{target.name} now has {target.hp} HP")
            print(f"{self.name} has {self.mana} mana left")
        else:
            # 魔法不够，治疗失败
            print(f"{self.name} has no mana!")
    
    # 重写父类的show_status方法（增加显示魔法值）
    def show_status(self):
        # 先调用父类的show_status，显示名字、等级、血量、攻击力
        super().show_status()
        # 再额外显示牧师的魔法值
        print(f"   Mana: {self.mana}")
    print("\n" + "="*60)
print("最终测试：团队战斗！")
print("="*60)

# 1. 创建三个角色
print("\n【创建角色】")
warrior = Warrior("Aragorn")      # 战士
mage = Mage("Gandalf")            # 法师
priest = Priest("Galadriel")      # 牧师

# 显示初始状态
warrior.show_status()
mage.show_status()
priest.show_status()

# 2. 创建一个敌人
print("\n【敌人出现】")
enemy = Warrior("Dark Lord")      # 黑暗领主当敌人
enemy.show_status()

# 3. 开始战斗
print("\n" + "="*60)
print("战斗开始！")
print("="*60)

# 战士嘲讽（保护队友）
print("\n>>> 战士嘲讽 <<<")
warrior.taunt(enemy)

# 法师放火球
print("\n>>> 法师火球术 <<<")
mage.fireball(enemy)

# 牧师治疗战士
print("\n>>> 牧师治疗 <<<")
priest.heal(warrior)

# 战士攻击
print("\n>>> 战士攻击 <<<")
warrior.attack_target(enemy)

# 敌人反击
print("\n>>> 敌人反击 <<<")
enemy.attack_target(warrior)

# 显示最终状态
print("\n" + "="*60)
print("战斗结束！最终状态：")
print("="*60)
warrior.show_status()
mage.show_status()
priest.show_status()
enemy.show_status()