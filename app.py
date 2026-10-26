from __future__ import annotations
import csv, hmac, html, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
import qrcode
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='Білім Дос — Рефлексия урока', page_icon='📚', layout='wide', initial_sidebar_state='collapsed')
DB = Path(__file__).with_name('bilim_dos.db')
MAX_CARDS = 24
DEFAULTS = {'school': 'Білім Дос', 'topic': 'Рефлексия урока', 'question': 'Что нового ты узнал(а) сегодня?'}

@contextmanager
def connect():
    con = sqlite3.connect(DB, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=20000')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init():
    with connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS responses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, answer TEXT NOT NULL, created TEXT NOT NULL)')
        con.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        con.executemany('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', DEFAULTS.items())

def settings():
    with connect() as con:
        result = dict(DEFAULTS)
        result.update({r['key']: r['value'] for r in con.execute('SELECT key,value FROM settings') if r['key'] in DEFAULTS})
        return result

def all_answers(limit=None):
    with connect() as con:
        if limit is None:
            return con.execute('SELECT * FROM responses ORDER BY id DESC').fetchall()
        return con.execute('SELECT * FROM responses ORDER BY id DESC LIMIT ?', (limit,)).fetchall()

def total_answers():
    with connect() as con:
        return con.execute('SELECT COUNT(*) FROM responses').fetchone()[0]

def clean(s):
    return ' '.join(str(s).split())

def add(name, answer):
    name, answer = clean(name), clean(answer)
    if not 2 <= len(name) <= 45:
        raise ValueError('Имя должно содержать от 2 до 45 символов.')
    if not 3 <= len(answer) <= 160:
        raise ValueError('Ответ должен содержать от 3 до 160 символов.')
    with connect() as con:
        con.execute('INSERT INTO responses(name,answer,created) VALUES (?,?,?)', (name, answer, datetime.now(timezone.utc).isoformat(timespec='seconds')))

def esc(s):
    return html.escape(str(s), quote=True)

def short(s, size):
    return s if len(s) <= size else s[:size-1].rstrip() + '…'

def urls():
    base = st.context.url.split('?', 1)[0].rstrip('/') + '/'
    return base, base + '?view=student', base + '?view=admin'

def qr(url):
    code = qrcode.QRCode(box_size=10, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    code.add_data(url)
    code.make(fit=True)
    output = BytesIO()
    code.make_image(fill_color='#3158C8', back_color='white').save(output, format='PNG')
    return output.getvalue()

CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&display=swap');
:root{--indigo:#365CD3;--deep:#203563;--sky:#EFF5FF;--muted:#60749C;--border:#E1E9FA;--mint:#E7F8F1}
*,*::before,*::after{box-sizing:border-box}
.stApp{background:radial-gradient(circle at 94% 2%,#DAE6FF 0,transparent 33%),linear-gradient(180deg,#F8FAFF 0%,#F1F5FF 100%);color:var(--deep)}
html,body,.stApp,.stApp button,.stApp input,.stApp textarea{font-family:'Nunito','DejaVu Sans',sans-serif}
.block-container{max-width:1380px;padding-top:1.15rem;padding-bottom:2.4rem}
[data-testid="stHeader"]{background:transparent!important}#MainMenu,footer{visibility:hidden}
.brand{font-size:1rem;font-weight:900;color:#4165CB;margin-bottom:16px;letter-spacing:.025em}
.hero{position:relative;isolation:isolate;overflow:hidden;border-radius:29px;padding:34px 40px;background:linear-gradient(112deg,#2D51B9 0%,#496FE0 63%,#7A83E8 100%);color:white;box-shadow:0 20px 38px #3A60B728}
.hero:after{content:'';position:absolute;z-index:-1;right:-120px;top:-120px;width:460px;height:460px;border:2px solid #FFFFFF28;border-radius:50%;box-shadow:0 0 0 55px #FFFFFF0B,0 0 0 112px #FFFFFF08}
.hero h1{color:#fff;font-size:clamp(2rem,3.45vw,3.15rem);font-weight:900;letter-spacing:-.028em;margin:8px 0 13px;line-height:1.13}
.hero p{color:#EAF0FF;font-size:1.035rem;line-height:1.65;margin:0;max-width:890px}
.hero .over{font-size:.78rem;letter-spacing:.115em;font-weight:900;color:#DCE7FF}
.hero strong{color:white;font-weight:900}
.kicker{color:var(--indigo);font-size:.78rem;font-weight:900;letter-spacing:.11em;margin-top:26px}
.heading{font-size:clamp(1.55rem,2.35vw,2.15rem);font-weight:900;color:var(--deep);margin-bottom:14px}
/* Общий экран и QR */
.qrtitle{text-align:center;font-size:1rem;font-weight:900;color:#3159C8;background:#fff;border:1px solid #E2EAF9;padding:12px 12px;border-radius:18px;box-shadow:0 8px 24px #385DA80A}
.qr-spacer{height:16px}
.live{color:#158569;background:#E7F8F2;border:1px solid #C9EEE1;border-radius:99px;font-weight:900;padding:7px 13px;font-size:.8rem;display:inline-block}
.count{font-weight:900;color:#5B719D;margin:12px 0}
/* Страница ученика */
.student-hero{padding:30px 40px 32px;min-height:208px;background:linear-gradient(105deg,#294CB2,#496DDD 66%,#8184E8)}
.student-hero h1{font-size:clamp(2.2rem,3.7vw,3.6rem);margin-top:8px;margin-bottom:13px}
.student-hero h1 .highlight{color:#FFDB84}
.student-hero p{font-size:1.06rem;line-height:1.7;max-width:860px}
.student-hero .hero-decoration{position:absolute;right:80px;top:31px;font-size:6.5rem;opacity:.2;transform:rotate(14deg);pointer-events:none}
.student-header{padding-top:29px;padding-bottom:11px}
.student-kicker{font-size:.74rem;letter-spacing:.135em;text-transform:uppercase;color:#5273D6;font-weight:900;margin-bottom:10px}
.student-heading{font-size:clamp(1.65rem,2.65vw,2.3rem);font-weight:900;letter-spacing:-.025em;color:var(--deep);line-height:1.18;margin-bottom:8px}
.student-subtitle{font-size:.96rem;color:var(--muted);line-height:1.55;max-width:680px}
.student-side{padding-top:30px}
/* Системная Streamlit form оформлена как собственная карточка */
[data-testid="stForm"]{background:#fff!important;border:1px solid #DDE7FC!important;border-radius:25px!important;padding:25px 27px 27px!important;box-shadow:0 16px 35px #2D4E9810!important}
.form-welcome{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:14px;margin-bottom:6px;border-bottom:1px solid #EDF1F9}
.form-welcome strong{color:#29447A;font-size:1.02rem;font-weight:900}
.form-welcome span{background:#EEF2FF;color:#5773BC;border-radius:100px;padding:5px 10px;font-size:.78rem;font-weight:900;white-space:nowrap}
.form-field-label{font-size:.96rem;line-height:1.5;font-weight:900;color:#2A416F;margin-top:13px;margin-bottom:8px}
.form-field-hint{color:#7A88AB;font-size:.78rem;line-height:1.4;margin-top:-1px;margin-bottom:2px}
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextArea"] [data-baseweb="textarea"]{background:#F8FAFF!important;border-radius:15px!important}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
  background:#F8FAFF!important;color:#263B63!important;border:1.5px solid #D9E3F6!important;
  border-radius:15px!important;box-shadow:none!important;font-size:1rem!important;
  transition:background .18s,border-color .18s,box-shadow .18s!important
}
[data-testid="stTextInput"] input{min-height:53px!important;padding:10px 16px!important}
[data-testid="stTextArea"] textarea{min-height:132px!important;padding:15px 16px!important;line-height:1.55!important}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{color:#93A0B9!important;opacity:1!important}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{
  background:#fff!important;border-color:#5275E5!important;outline:none!important;
  box-shadow:0 0 0 4px #4E77E322!important
}
[data-testid="stWidgetLabel"] p{color:#2A416F!important;font-weight:800!important}
.form-privacy{background:#F0F7FF;border:1px solid #E1EDFE;color:#61769D;padding:12px 14px;border-radius:12px;font-size:.83rem;line-height:1.55;margin-top:14px;margin-bottom:12px}
.stButton button,.stDownloadButton button,.stLinkButton a{border-radius:14px!important;font-weight:900!important;min-height:3rem;transition:transform .15s,box-shadow .2s,background .2s!important}
[data-testid="stFormSubmitButton"] button,[data-testid="stBaseButton-primaryFormSubmit"]{
  background:linear-gradient(100deg,#325AD2,#5675E8)!important;border:1px solid transparent!important;
  color:white!important;min-height:54px!important;font-size:1rem!important;
  box-shadow:0 9px 20px #375ECC2B!important
}
[data-testid="stFormSubmitButton"] button:hover,[data-testid="stBaseButton-primaryFormSubmit"]:hover{
 background:linear-gradient(100deg,#254CC4,#4366DE)!important;box-shadow:0 12px 25px #375ECC40!important;transform:translateY(-1px)
}
[data-testid="stFormSubmitButton"] button:focus-visible,[data-testid="stBaseButton-primaryFormSubmit"]:focus-visible{outline:3px solid #9BB1FF!important;outline-offset:3px}
.stLinkButton a{background:#fff!important;border:1.5px solid #D8E4FA!important;color:#3158C8!important}
.stLinkButton a:hover{background:#EDF3FF!important;border-color:#B6CAF6!important;transform:translateY(-1px)}
/* Шаги и памятка */
.side-card{background:white;border:1px solid #DFE8FB;border-radius:23px;padding:24px 26px;margin:0 0 20px;box-shadow:0 12px 30px #2D4E980C;color:#4E638D}
.side-card.soft{background:linear-gradient(145deg,#FDFEFF,#EDF5FF)}
.side-heading{display:flex;gap:12px;align-items:center;font-size:1.08rem;font-weight:900;color:#294376;margin:0 0 19px}
.side-icon{width:43px;height:43px;min-width:43px;display:inline-grid;place-items:center;border-radius:15px;background:#EFF1FF;font-size:1.35rem}
.side-step{display:flex;align-items:flex-start;gap:13px;margin-bottom:17px}
.side-step:last-of-type{margin-bottom:7px}
.step-index{width:29px;height:29px;min-width:29px;display:grid;place-items:center;border-radius:50%;background:#EAF0FF;color:#3B62D0;font-weight:900;font-size:.83rem}
.step-text{font-size:.93rem;line-height:1.48;color:#50648E;padding-top:3px}
.side-note{border-top:1px solid #EDF1F8;margin-top:18px;padding-top:16px;font-size:.88rem;line-height:1.65;color:#62769B}
.side-card.safety{background:#F5FBF9;border-color:#D8EFE7}
.side-card.safety .side-icon{background:#E2F5EE}
.side-card.safety .side-heading{margin-bottom:8px}
.side-card.safety p{margin:0;font-size:.92rem;color:#52766C;line-height:1.65}
.panel{background:white;border:1px solid #DCE5F9;border-radius:23px;padding:18px 23px;margin:15px 0;color:#45618C;line-height:1.8}
.panel b{color:#263967}
.footer{text-align:center;font-weight:900;color:#8195C0;padding:24px 0}
@media(max-width:840px){
 .block-container{padding:1rem .85rem 1.7rem}
 .hero{padding:25px 23px;border-radius:22px}
 .student-hero{min-height:unset;padding:27px 22px}
 .student-hero h1{font-size:2.25rem}
 .student-hero .hero-decoration{right:-20px;top:40px;font-size:4rem}
 .student-header{padding-top:23px;padding-bottom:4px}
 .student-side{padding-top:3px}
 [data-testid="stForm"]{padding:20px 18px 24px!important;border-radius:21px!important}
 .side-card{padding:20px 20px;margin-top:5px}
 .qr-spacer{height:17px}
}
@media(prefers-reduced-motion:reduce){.stButton button,.stLinkButton a{transition:none!important}}
</style>''' 

POSITIONS = ([(x, 90) for x in (275, 495, 715, 935, 1155)]
             + [(140,y) for y in (200,300,400,500,600,700,800)]
             + [(1290,y) for y in (200,300,400,500,600,700,800)]
             + [(x,820) for x in (275,495,715,935,1155)])
PALETTE = [('#365FCF','#EDF2FF'),('#E68A42','#FFF2E5'),('#139C89','#E5F8F5'),('#BA619D','#FFF0F8'),('#8570D1','#F2EEFF'),('#D26E62','#FFF0EC')]

def cluster(rows, fresh, school):
    lines, cards = [], []
    for r,(x,y) in zip(reversed(rows), POSITIONS):
        name, answer, ident = clean(r['name']),clean(r['answer']),int(r['id'])
        accent,paper = PALETTE[(ident-1)%len(PALETTE)]
        new = ' fresh' if ident in fresh else ''
        lines.append(f'<path class="ray{new}" d="M720 455 Q{(720+x)/2:.0f} {(455+y)/2-35:.0f} {x} {y}" fill="none" stroke="{accent}" stroke-width="3" stroke-dasharray="7 9" opacity=".48"/>')
        cards.append(f'<g class="note{new}" transform="translate({x} {y})" tabindex="0"><title>{esc(name)} — {esc(answer)}</title><rect x="-100" y="-35" width="200" height="70" rx="17" fill="{paper}" stroke="{accent}" stroke-width="2.6"/><circle cx="-82" cy="-20" r="5" fill="{accent}"/><text x="0" y="-3" class="answer" text-anchor="middle">{esc(short(answer,24))}</text><text x="0" y="20" class="name" text-anchor="middle" fill="{accent}">{esc(short(name,23))}</text></g>')
    # Учебник и добрый школьный персонаж в центре схемы.
    center=f'''<g class="mascot"><ellipse cx="720" cy="620" rx="218" ry="29" fill="#BACAF0" opacity=".35"/>
      <path d="M510 490 Q620 453 720 515 Q820 453 930 490 L930 626 Q820 594 720 649 Q620 594 510 626Z" fill="white" stroke="#355BC4" stroke-width="9"/>
      <path d="M720 515V648" stroke="#355BC4" stroke-width="7"/><path d="M536 517Q630 496 690 540 M536 544Q630 523 690 565 M750 540Q820 495 904 517 M750 565Q830 524 904 543" fill="none" stroke="#DCE6FF" stroke-width="7" stroke-linecap="round"/>
      <path d="M720 515V428" stroke="#FFB44D" stroke-width="15" stroke-linecap="round"/>
      <circle cx="720" cy="355" r="87" fill="#FFD577" stroke="#DC9846" stroke-width="7"/>
      <path d="M650 305Q720 264 790 305" fill="none" stroke="#A05E35" stroke-width="11" stroke-linecap="round"/>
      <circle cx="689" cy="353" r="7" fill="#4B3E45"/><circle cx="752" cy="353" r="7" fill="#4B3E45"/><path d="M690 383Q721 410 752 383" fill="none" stroke="#A75E58" stroke-width="7" stroke-linecap="round"/>
      <circle cx="666" cy="374" r="13" fill="#FBA89B" opacity=".75"/><circle cx="772" cy="374" r="13" fill="#FBA89B" opacity=".75"/>
      <path d="M642 288L720 241 798 288 720 321Z" fill="#3158C8" stroke="#24499F" stroke-width="5"/><path d="M780 289V333" stroke="#24499F" stroke-width="6"/><circle cx="780" cy="337" r="9" fill="#FFB44D"/>
      <path d="M647 290V270Q719 238 793 270V293" fill="none" stroke="#3158C8" stroke-width="17"/>
      <path d="M610 460Q563 424 541 453 M828 460Q871 424 898 453" fill="none" stroke="#3158C8" stroke-width="12" stroke-linecap="round"/></g>
      <rect x="555" y="657" width="330" height="72" rx="30" fill="#3158C8" stroke="white" stroke-width="5"/>
      <text x="720" y="704" text-anchor="middle" font-size="30" font-weight="900" fill="white">{esc(short(school,25))}</text>
      <text x="720" y="766" text-anchor="middle" font-size="23" font-weight="800" fill="#405F9F">Наши мысли после урока</text>'''
    source = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>' + '''
    html,body{padding:0;margin:0;width:100%;height:100%;overflow:hidden;background:#EFF5FF}
    svg{display:block;width:100%;height:100%;font-family:Arial,'DejaVu Sans',sans-serif}
    .answer{font-size:17px;font-weight:800;fill:#263967}.name{font-size:13px;font-weight:700}
    .note{cursor:help;filter:drop-shadow(0 4px 7px #233A6518)}
    .note:hover,.note:focus{filter:drop-shadow(0 5px 14px #29447C50);outline:none}
    .note.fresh{animation:pop .85s cubic-bezier(.16,1.3,.36,1) both;transform-box:fill-box;transform-origin:center}
    .ray.fresh{animation:fade .85s ease-out both}
    @keyframes pop{from{opacity:0;scale:.6}to{opacity:1;scale:1}}
    @keyframes fade{from{opacity:0}to{opacity:.48}}
    @media(prefers-reduced-motion:reduce){.note.fresh,.ray.fresh{animation:none}}
    '''+'</style></head><body><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" aria-label="Интерактивные ответы учеников" role="img"><defs><radialGradient id="bg"><stop stop-color="white"/><stop offset="1" stop-color="#ECF3FF"/></radialGradient><pattern id="dots" width="42" height="42" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r="2" fill="#B8C9E8" opacity=".45"/></pattern></defs><rect width="1440" height="900" rx="30" fill="url(#bg)"/><rect width="1440" height="900" rx="30" fill="url(#dots)"/><circle cx="720" cy="460" r="263" fill="#F8FAFF" stroke="#DAE5FC" stroke-width="3" stroke-dasharray="9 12"/>' + ''.join(lines)+center+''.join(cards)+'</svg></body></html>'
    components.html(source, height=690, scrolling=False)

def header(label, s):
    st.markdown(f'<div class="brand">📚 {esc(s["school"])} &nbsp;·&nbsp; {esc(label)}</div>',unsafe_allow_html=True)

def wall(student_url):
    s=settings();header('ОБЩИЙ ЭКРАН',s)
    left,right=st.columns([4.6,1.2],gap='large',vertical_alignment='center')
    with left:
        st.markdown(f'<div class="hero"><div class="over">✨ НАШ ШКОЛЬНЫЙ УРОК</div><h1>{esc(s["topic"])} 💭</h1><p>{esc(s["question"])} Поделись мыслью — она появится на нашем общем экране!</p></div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="qrtitle">📱 Сканируй и отвечай</div>',unsafe_allow_html=True)
        st.image(qr(student_url),use_container_width=True)
        st.markdown('<div class="qr-spacer" aria-hidden="true"></div>',unsafe_allow_html=True)
        st.link_button('✍️ Написать ответ',student_url,use_container_width=True)
    st.markdown('<div class="kicker">НАША ОБЩАЯ РЕФЛЕКСИЯ</div><div class="heading">Каждая мысль важна 🌟</div>',unsafe_allow_html=True)
    @st.fragment(run_every='3s')
    def live():
        recent=all_answers(MAX_CARDS);count=total_answers()
        ids={int(r['id']) for r in recent};old=st.session_state.get('previous_ids')
        fresh=ids-old if old is not None else set();st.session_state['previous_ids']=ids
        st.markdown(f'<div class="count">💬 Всего ответов: {count} · На экране: {len(recent)} &nbsp; <span class="live">● Обновление каждые 3 секунды</span></div>',unsafe_allow_html=True)
        cluster(recent,fresh,s['school'])
        if not count: st.info('✨ Здесь скоро появятся первые ответы!')
        if count>MAX_CARDS: st.caption(f'Показаны последние {MAX_CARDS} ответов из {count}. Все ответы доступны учителю.')
        with st.expander('📃 Смотреть ответы списком'):
            for r in recent: st.markdown(f'**{esc(r["name"])}:** {esc(r["answer"])}')
    live()
    st.markdown('<div class="footer">💙 УЧИМСЯ · ДЕЛИМСЯ · РАСТЁМ ВМЕСТЕ 💛</div>',unsafe_allow_html=True)

def student(wall_url):
    s=settings()
    header('СТРАНИЦА УЧЕНИКА',s)
    st.markdown(
        '<div class="hero student-hero">'
        '<div class="over">✨ МАЛЕНЬКОЕ МНЕНИЕ — БОЛЬШОЕ ЗНАЧЕНИЕ</div>'
        '<h1>Твой голос <span class="highlight">важен!</span> 🌟</h1>'
        f'<p><strong>Вопрос урока:</strong> {esc(s["question"])}<br>'
        'Расскажи о своих впечатлениях, а мы добавим твою мысль на общий экран класса.</p>'
        '<div class="hero-decoration" aria-hidden="true">✏️</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    left,right=st.columns([1.7,1],gap='large',vertical_alignment='top')
    with left:
        st.markdown(
            '<div class="student-header">'
            '<div class="student-kicker">💬 ТВОЯ РЕФЛЕКСИЯ</div>'
            '<div class="student-heading">Поделись впечатлением ✨</div>'
            '<div class="student-subtitle">Напиши пару слов об уроке — каждое мнение поможет нам стать лучше.</div>'
            '</div>',unsafe_allow_html=True
        )
        with st.form('send',clear_on_submit=True,border=True):
            st.markdown(
                '<div class="form-welcome"><strong>📝 Мой отзыв об уроке</strong>'
                '<span>2 простых шага</span></div>',unsafe_allow_html=True
            )
            st.markdown('<div class="form-field-label">👤 Как тебя зовут?</div>',unsafe_allow_html=True)
            name=st.text_input(
                'Имя ученика',placeholder='Например, Алина',max_chars=45,
                label_visibility='collapsed'
            )
            st.markdown('<div class="form-field-label">💭 Что ты думаешь об уроке?</div>',unsafe_allow_html=True)
            answer=st.text_area(
                'Отзыв об уроке',
                placeholder='Сегодня я узнал(а)…\nБольше всего мне понравилось…\nЯ хотел(а) бы ещё узнать…',
                max_chars=160,height=142,label_visibility='collapsed'
            )
            st.markdown(
                '<div class="form-privacy">🔐 Твой ответ увидят другие ученики. '
                'Не указывай номер телефона, адрес или другие личные данные.</div>',
                unsafe_allow_html=True
            )
            send=st.form_submit_button(
                '🚀 Отправить мой ответ',type='primary',use_container_width=True
            )
        if send:
            try:
                add(name,answer)
            except ValueError as e:
                st.warning(str(e))
            except sqlite3.Error:
                st.error('Ошибка сохранения. Попробуй ещё раз.')
            else:
                st.success('🎉 Готово! Твой ответ появился на общем экране.')
                st.balloons()
        st.link_button('👀 Посмотреть ответы нашего класса',wall_url,use_container_width=True)
    with right:
        st.markdown(
            '<div class="student-side">'
            '<div class="side-card">'
            '<div class="side-heading"><span class="side-icon">🌈</span>Как это работает?</div>'
            '<div class="side-step"><span class="step-index">1</span>'
            '<span class="step-text">Напиши своё имя.</span></div>'
            '<div class="side-step"><span class="step-index">2</span>'
            '<span class="step-text">Поделись тем, что узнал(а), что понравилось или осталось непонятным.</span></div>'
            '<div class="side-step"><span class="step-index">3</span>'
            '<span class="step-text">Нажми «Отправить мой ответ» — и увидишь его на общем экране.</span></div>'
            '<div class="side-note">💡 Здесь нет неправильных ответов. Самое главное — <b>твоё собственное мнение!</b></div>'
            '</div>'
            '<div class="side-card safety">'
            '<div class="side-heading"><span class="side-icon">🛡️</span>Делимся безопасно</div>'
            '<p>Будь уважительным к другим и не публикуй личную информацию.</p>'
            '</div></div>',unsafe_allow_html=True
        )

def teacher_password():
    try:return str(st.secrets['ADMIN_PASSWORD']).strip()
    except(KeyError,FileNotFoundError):return os.getenv('ADMIN_PASSWORD','').strip()

def export(rows):
    out=StringIO();writer=csv.writer(out)
    writer.writerow(['№','Имя ученика','Ответ','Время (UTC)'])
    for r in rows:
        values=[r['id'],r['name'],r['answer'],r['created']]
        writer.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in values])
    return out.getvalue().encode('utf-8-sig')

def admin(wall_url):
    s=settings();header('ПАНЕЛЬ УЧИТЕЛЯ',s)
    st.markdown('<div class="heading">🔒 Управление рефлексией</div>',unsafe_allow_html=True)
    password=teacher_password()
    if not password:
        st.warning('Добавьте ADMIN_PASSWORD в Streamlit Cloud → App settings → Secrets.')
        st.code('ADMIN_PASSWORD = "ваш_сложный_пароль"',language='toml');return
    if not st.session_state.get('authorized',False):
        with st.form('login'):
            attempt=st.text_input('Пароль учителя',type='password')
            login=st.form_submit_button('Войти',type='primary')
        if login:
            if hmac.compare_digest(attempt,password):st.session_state['authorized']=True;st.rerun()
            else:st.error('Неверный пароль.')
        return
    if st.button('🔒 Выйти'):st.session_state['authorized']=False;st.rerun()
    st.subheader('✏️ Настройки урока')
    with st.form('config'):
        school=st.text_input('Название проекта / школы',s['school'],max_chars=45)
        topic=st.text_input('Название урока',s['topic'],max_chars=90)
        question=st.text_input('Вопрос для рефлексии',s['question'],max_chars=170)
        save=st.form_submit_button('💾 Сохранить',type='primary')
    if save:
        if not all([clean(school),clean(topic),clean(question)]):st.warning('Все поля обязательны.')
        else:
            with connect() as con:
                con.executemany('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', [('school',clean(school)),('topic',clean(topic)),('question',clean(question))])
            st.rerun()
    data=all_answers();st.metric('💬 Ответы учеников',len(data))
    st.download_button('⬇️ Скачать все ответы (CSV)',export(data),file_name='bilim_dos_reflection.csv',mime='text/csv',disabled=not data,use_container_width=True)
    st.divider()
    st.subheader('🗑️ Удалить ответ')
    if data:
        lookup={r['id']:r for r in data}
        selected=st.selectbox('Выберите ответ',list(lookup),format_func=lambda i:f'#{i} · {lookup[i]["name"]} · {short(lookup[i]["answer"],40)}')
        if st.button('Удалить выбранный ответ'):
            with connect() as con:con.execute('DELETE FROM responses WHERE id=?',(selected,))
            st.rerun()
    else:st.info('Ответов пока нет.')
    st.divider();st.subheader('🧹 Начать новую рефлексию')
    confirm=st.checkbox('Подтверждаю удаление всех ответов.')
    if st.button('Очистить все ответы',disabled=not confirm or not data):
        with connect() as con:con.execute('DELETE FROM responses')
        st.rerun()
    st.info('На бесплатном Streamlit Cloud SQLite не гарантирует постоянное хранение. Сохраняйте CSV после урока.')
    st.link_button('↗ Открыть общий экран',wall_url)

def main():
    init();st.markdown(CSS,unsafe_allow_html=True)
    wall_url,student_url,_=urls()
    view=st.query_params.get('view','wall')
    if view=='student':student(wall_url)
    elif view=='admin':admin(wall_url)
    else:wall(student_url)

if __name__=='__main__':main()
