"""Cut approved generated 4x2 sheets into lightweight reaction images."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / 'moso-pack'
REACTIONS = [
 ('你好','neutral','acknowledge','挥手打招呼','问好 招呼 嗨'),
 ('收到','neutral','acknowledge','抬手OK确认收到','确认 收到 明白'),
 ('没问题','happy','acknowledge','双手点赞表示同意','可以 没问题 好的'),
 ('谢谢','grateful','thanks','手放胸口鞠躬感谢','感激 感谢 谢谢'),
 ('太棒了','happy','celebrate','双手鼓掌称赞','厉害 太棒了 赞'),
 ('搞定','happy','celebrate','双拳举起庆祝完成','完成 搞定 成功 跑通'),
 ('加油','encouraging','support','向前握拳打气','鼓励 加油 努力'),
 ('给你比心','happy','thanks','双手捧橙色爱心','比心 喜欢 爱心 谢谢'),
 ('让我想想','confused','question','托腮思考','思考 想想 琢磨'),
 ('啊？','confused','question','摊手歪头疑惑','疑惑 什么 啊 不懂'),
 ('这合理吗','confused','question','双臂展开表示不可思议','合理 疑惑 离谱'),
 ('无语了','speechless','tease','扶额无奈','无语 无奈 汗颜'),
 ('真的吗','surprised','question','抱臂侧头怀疑','真的 确认 怀疑'),
 ('我看看','neutral','acknowledge','俯身抬手遮眉观察','查看 检查 看看'),
 ('等一下','neutral','wait','看手腕上的表','等待 等一下 稍等'),
 ('正在处理','neutral','wait','专注操作笔记本电脑','处理 正在忙 工作 写代码'),
 ('哈哈哈','happy','celebrate','弯腰捂腹大笑','好笑 哈哈 笑死'),
 ('震惊','surprised','question','后仰双手举起惊讶','震惊 惊讶 意外'),
 ('是我吗','confused','question','指向自己略显尴尬','是我 指我 叫我'),
 ('我尽力了','sad','empathize','耸肩摊手无奈','尽力 无奈 失败'),
 ('对不起','sad','apologize','低头双手相握致歉','抱歉 道歉 对不起'),
 ('委屈','sad','empathize','双手放胸前带泪滴符号','委屈 难过 伤心'),
 ('累了','sad','empathize','趴在桌子上休息','疲惫 累 休息'),
 ('悄悄围观','playful','wait','从边缘探出兔头围观','围观 吃瓜 偷看'),
 ('喝口水','neutral','support','举白色杯子喝水','喝水 休息 缓缓'),
 ('回头见','happy','acknowledge','正面略侧身自然抬臂挥手告别','再见 拜拜 回头见'),
 ('早上好','happy','acknowledge','伸展双臂迎接早晨','早安 早上好 问好'),
 ('晚安','neutral','acknowledge','合掌枕脸睡觉','晚安 睡觉 休息'),
 ('安排上了','happy','acknowledge','双手指向前方自信回应','安排 可以 好的'),
 ('别急','encouraging','support','伸出手掌温和安抚','别急 放松 慢慢来'),
 ('我在呢','encouraging','support','伸出拳头碰拳陪伴','陪伴 我在 支持'),
 ('下班啦','happy','celebrate','举复古麦克风和拳头庆祝','下班 收工 完成'),
]


def main():
    assets = PACK / 'assets'
    assets.mkdir(exist_ok=True)
    records = []
    thumbs = []
    for batch, letter in enumerate('abcd'):
        sheet = Image.open(PACK / 'sheets' / f'{letter}.png').convert('RGB')
        w, h = sheet.size
        for position in range(8):
            number = batch * 8 + position
            caption, emotion, intent, pose, tags = REACTIONS[number]
            row, column = divmod(position, 4)
            cell = sheet.crop((round(column*w/4), round(row*h/2), round((column+1)*w/4), round((row+1)*h/2)))
            override = PACK / 'overrides' / f'moso-{number+1:02d}.png'
            if override.exists():
                cell = Image.open(override).convert('RGB')
            cell = ImageOps.fit(cell, (384,384), method=Image.Resampling.LANCZOS)
            target = assets / f'moso-{number+1:02d}.jpg'
            cell.save(target, quality=87, optimize=True)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            caution = ['严肃冲突','用户痛苦倾诉'] if intent == 'tease' else []
            if caption in {'搞定','安排上了','正在处理','下班啦'}:
                caution.append('不可用表情代替真实执行状态或承诺')
            if caption == '给你比心':
                caution.append('不适合亲昵表达的正式场合')
            records.append(dict(id=digest,file=str(target.relative_to(PACK)),description=f'MoSo白色折纸兔头、黑西装、橙色背景；{pose}',meaning=caption+'，通过动作表达对应语气',text=caption,emotions=[emotion],intents=[intent],tags=['MoSo','moso',*tags.split()],relationships=['friend','熟悉同事'],avoid=caution,sarcasm='possible' if intent=='tease' else 'none',source='基于用户提供的MoSo形象参考，由内置imagegen生成；母版网格分切，第26枚使用独立动作修正版',rights='用户授权本次制作、本地使用及上传其GitHub仓库；未另行授予第三方商业再分发权'))
            thumbs.append(cell.resize((192,192),Image.Resampling.LANCZOS))
    (PACK / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2),encoding='utf-8')
    overview = Image.new('RGB',(8*192,4*192))
    for i,thumb in enumerate(thumbs):
        overview.paste(thumb,((i%8)*192,(i//8)*192))
    overview.save(PACK/'overview.jpg',quality=92)
    sizes=[(PACK/r['file']).stat().st_size for r in records]
    print(json.dumps({'count':len(records),'unique':len({r['id'] for r in records}),'dimensions':[384,384],'min_bytes':min(sizes),'max_bytes':max(sizes),'total_bytes':sum(sizes)},ensure_ascii=False))


if __name__ == '__main__':
    main()
