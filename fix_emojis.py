#!/usr/bin/env python3
"""
修复脚本：替换所有表情符号为文本表示，解决Windows编码问题
"""

import os
import re
from pathlib import Path

# 定义表情符号映射
EMOJI_MAPPINGS = {
    '🕷️': '[SPIDER]',
    '✅': '[OK]',
    '❌': '[X]',
    '⚠️': '[WARN]',
    '🔄': '[RETRY]',
    '🎲': '[DICE]',
    '📊': '[CHART]',
    '📝': '[NOTE]',
    '⚡': '[FAST]',
    '🔒': '[LOCK]',
    '🔍': '[SEARCH]',
    '📂': '[FOLDER]',
    '⚙️': '[GEAR]',
    '🏁': '[FLAG]',
    '🎯': '[TARGET]',
    '📋': '[CLIPBOARD]',
    '📤': '[OUTBOX]',
    '📥': '[INBOX]',
    '🔄': '[REFRESH]',
    '✅': '[CHECK]',
    '⏹️': '[STOP]',
    '🚀': '[ROCKET]',
    '🌐': '[GLOBE]',
    '🧩': '[PUZZLE]',
    '🧠': '[BRAIN]',
    '🔧': '[TOOL]',
    '📊': '[STATS]',
    '📈': '[GRAPH]',
    '📁': '[DIR]',
    '📄': '[FILE]',
    '🔗': '[LINK]',
    '🖥️': '[COMPUTER]',
    '📱': '[PHONE]',
    '⏱️': '[TIMER]',
    '⏸️': '[PAUSE]',
    '▶️': '[PLAY]',
    '⏹️': '[STOP]',
    '⏭️': '[NEXT]',
    '⏮️': '[PREV]',
    '🔁': '[REPEAT]',
    '🔀': '[SHUFFLE]',
    '🔊': '[SOUND]',
    '🔇': '[MUTE]',
    '🔔': '[BELL]',
    '🔕': '[NOBELL]',
    '💡': '[BULB]',
    '📌': '[PIN]',
    '📍': '[LOCATION]',
    '📎': '[CLIP]',
    '📏': '[RULER]',
    '📐': '[TRIANGLE]',
    '🔨': '[HAMMER]',
    '🛠️': '[TOOLS]',
    '🔧': '[WRENCH]',
    '🔩': '[BOLT]',
    '⚙️': '[COG]',
    '🗜️': '[CLAMP]',
    '🔬': '[MICROSCOPE]',
    '🔭': '[TELESCOPE]',
    '📡': '[SATELLITE]',
    '💉': '[SYRINGE]',
    '💊': '[PILL]',
    '🩹': '[BANDAGE]',
    '🩺': '[STETHOSCOPE]',
    '🌡️': '[THERMOMETER]',
    '🧹': '[BROOM]',
    '🧻': '[ROLL]',
    '🧼': '[SOAP]',
    '🪥': '[TOOTHBRUSH]',
    '🧽': '[SPONGE]',
    '🪣': '[BUCKET]',
    '🧯': '[FIREEXTINGUISHER]',
    '🛒': '[CART]',
    '📦': '[PACKAGE]',
    '🏷️': '[LABEL]',
    '🔖': '[BOOKMARK]',
    '💸': '[MONEY]',
    '💳': '[CARD]',
    '🧾': '[RECEIPT]',
    '✉️': '[ENVELOPE]',
    '📧': '[EMAIL]',
    '📨': '[INCOMING]',
    '📩': '[ENVELOPE_ARROW]',
    '📤': '[OUTBOX]',
    '📥': '[INBOX]',
    '📦': '[PACKAGE]',
    '📫': '[MAILBOX]',
    '📪': '[MAILBOX_CLOSED]',
    '📬': '[MAILBOX_OPEN]',
    '📭': '[MAILBOX_EMPTY]',
    '📮': '[POSTBOX]',
    '🗳️': '[BALLOT]',
    '✏️': '[PENCIL]',
    '✒️': '[PEN]',
    '🖋️': '[FOUNTAIN_PEN]',
    '🖊️': '[PEN2]',
    '🖌️': '[BRUSH]',
    '🖍️': '[CRAYON]',
    '📝': '[MEMO]',
    '💼': '[BRIEFCASE]',
    '📁': '[FOLDER]',
    '📂': '[FOLDER_OPEN]',
    '🗂️': '[CARD_INDEX]',
    '📅': '[CALENDAR]',
    '📆': '[TEAROFF_CALENDAR]',
    '🗒️': '[NOTEPAD]',
    '🗓️': '[SPIRAL_CALENDAR]',
    '📇': '[CARD_BOX]',
    '📈': '[CHART_UP]',
    '📉': '[CHART_DOWN]',
    '📊': '[BAR_CHART]',
    '📋': '[CLIPBOARD]',
    '📌': '[PUSH_PIN]',
    '📍': '[ROUND_PIN]',
    '📎': '[PAPERCLIP]',
    '🖇️': '[PAPERCLIPS]',
    '📏': '[RULER_STRAIGHT]',
    '📐': '[RULER_TRIANGULAR]',
    '✂️': '[SCISSORS]',
    '🗃️': '[CARD_FILE_BOX]',
    '🗄️': '[FILE_CABINET]',
    '🗑️': '[WASTEBASKET]',
    '🔒': '[LOCK]',
    '🔓': '[UNLOCK]',
    '🔏': '[LOCK_PEN]',
    '🔐': '[LOCK_KEY]',
    '🔑': '[KEY]',
    '🗝️': '[OLD_KEY]',
    '🔨': '[HAMMER]',
    '🪓': '[AXE]',
    '⛏️': '[PICK]',
    '⚒️': '[HAMMER_PICK]',
    '🛠️': '[HAMMER_WRENCH]',
    '🗡️': '[DAGGER]',
    '⚔️': '[CROSSED_SWORDS]',
    '🔫': '[PISTOL]',
    '🪃': '[BOOMERANG]',
    '🏹': '[BOW_ARROW]',
    '🛡️': '[SHIELD]',
    '🪚': '[CARPENTRY_SAW]',
    '🔧': '[WRENCH]',
    '🪛': '[SCREWDRIVER]',
    '🔩': '[NUT_BOLT]',
    '⚙️': '[GEAR]',
    '🗜️': '[CLAMP]',
    '⚖️': '[SCALES]',
    '🦯': '[PROBING_CANE]',
    '🔗': '[LINK]',
    '⛓️': '[CHAINS]',
    '🧰': '[TOOLBOX]',
    '🧲': '[MAGNET]',
    '🪜': '[LADDER]',
    '⚗️': '[ALEMBIC]',
    '🧪': '[TEST_TUBE]',
    '🧫': '[PETRI_DISH]',
    '🧬': '[DNA]',
    '🔬': '[MICROSCOPE]',
    '🔭': '[TELESCOPE]',
    '📡': '[SATELLITE_ANTENNA]',
    '💉': '[SYRINGE]',
    '🩸': '[BLOOD_DROP]',
    '💊': '[PILL]',
    '🩹': '[ADHESIVE_BANDAGE]',
    '🩺': '[STETHOSCOPE]',
    '🚪': '[DOOR]',
    '🛗': '[ELEVATOR]',
    '🪞': '[MIRROR]',
    '🪟': '[WINDOW]',
    '🛏️': '[BED]',
    '🛋️': '[COUCH]',
    '🪑': '[CHAIR]',
    '🚽': '[TOILET]',
    '🪠': '[PLUNGER]',
    '🚿': '[SHOWER]',
    '🛁': '[BATHTUB]',
    '🪤': '[MOUSE_TRAP]',
    '🪒': '[RAZOR]',
    '🧴': '[LOTION]',
    '🧷': '[SAFETY_PIN]',
    '🧹': '[BROOM]',
    '🧻': '[ROLL_OF_PAPER]',
    '🪣': '[BUCKET]',
    '🧼': '[SOAP]',
    '🫧': '[BUBBLES]',
    '🪥': '[TOOTHBRUSH]',
    '🧽': '[SPONGE]',
    '🧯': '[FIRE_EXTINGUISHER]',
    '🛒': '[SHOPPING_CART]',
    '[DICE]': '[RANDOM]',
    '[WARN]': '[WARNING]',
    '[REFRESH]': '[RELOAD]',
    '[BAR_CHART]': '[CHART]',
}

def fix_file_emojis(file_path):
    """修复单个文件中的表情符号"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换所有表情符号
        for emoji, text in EMOJI_MAPPINGS.items():
            content = content.replace(emoji, text)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已修复: {file_path}")
            return True
        else:
            print(f"无需修复: {file_path}")
            return False
            
    except Exception as e:
        print(f"处理文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    project_dir = Path(__file__).parent
    fixed_count = 0
    
    # 需要修复的文件列表
    files_to_fix = [
        project_dir / 'run_crawler.py',
        project_dir / 'scripts' / 'spider_scheduler.py',
    ]
    
    print("开始修复表情符号编码问题...")
    
    for file_path in files_to_fix:
        if file_path.exists():
            if fix_file_emojis(file_path):
                fixed_count += 1
        else:
            print(f"文件不存在: {file_path}")
    
    print(f"\n修复完成! 共修复了 {fixed_count} 个文件。")
    print("现在可以在Windows上正常运行爬虫了。")

if __name__ == '__main__':
    main()