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
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
.stApp {background:radial-gradient(circle at top right,#DBE7FF,transparent 42%),#F8FAFF;color:#263967}
.stApp,.stApp button,.stApp input,.stApp textarea{font-family:Nunito,'DejaVu Sans',sans-serif}
.block-container{max-width:1420px;padding-top:1rem;padding-bottom:2rem}
[data-testid="stHeader"]{background:transparent} #MainMenu,footer{visibility:hidden}
.brand{font-size:1.06rem;font-weight:900;color:#3158C8;margin-bottom:14px}
.hero{border-radius:27px;padding:29px 34px;background:linear-gradient(115deg,#244AB4,#456CE0 70%,#7788E9);color:white;box-shadow:0 14px 35px #294D9D27}
.hero h1{color:white;font-size:clamp(1.9rem,3.5vw,3.2rem);font-weight:900;margin:6px 0 12px;line-height:1.2}
.hero p{color:#F0F4FF;font-size:1.05rem;line-height:1.6;margin:0}
.hero .over{font-size:.76rem;letter-spacing:.11em;font-weight:900;color:#E1E9FF}
.kicker{color:#3158C8;font-size:.8rem;font-weight:900;letter-spacing:.1em;margin-top:23px}
.heading{font-size:clamp(1.5rem,2.5vw,2.2rem);font-weight:900;color:#263967;margin-bottom:13px}
.panel{background:white;border:1px solid #DCE5F9;border-radius:23px;padding:18px 23px;margin:15px 0;color:#45618C;line-height:1.8}
.panel b{color:#263967}
.qrtitle{text-align:center;font-weight:900;color:#3158C8;background:white;padding:9px;border-radius:17px}
.live{color:#197D69;background:#E9F8F2;border-radius:99px;font-weight:900;padding:7px 13px;font-size:.82rem;display:inline-block}
.count{font-weight:900;color:#5B719D;margin:11px 0}
.stButton button,.stDownloadButton button,.stLinkButton a{border-radius:13px;font-weight:900;min-height:2.9rem}
[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#3158C8;color:white;border:0}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{border:1.5px solid #CDDAF6;border-radius:13px}
.footer{text-align:center;font-weight:900;color:#8195C0;padding:24px 0}
@media(max-width:700px){.hero{padding:22px}.block-container{padding:.9rem .7rem}}
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
    s=settings();header('СТРАНИЦА УЧЕНИКА',s)
    st.markdown(f'<div class="hero"><div class="over">👋 ПРИВЕТ, ДРУГ!</div><h1>Твой голос важен! 🌟</h1><p>{esc(s["question"])} Напиши, что ты думаешь: твоя мысль станет частью общей картины класса.</p></div>',unsafe_allow_html=True)
    left,right=st.columns([1.8,1],gap='large')
    with left:
        st.markdown('<div class="kicker">ВРЕМЯ ПОДВЕСТИ ИТОГИ</div><div class="heading">Поделись впечатлением ✨</div>',unsafe_allow_html=True)
        with st.form('send',clear_on_submit=True):
            name=st.text_input('👤 Как тебя зовут?',placeholder='Например: Алина',max_chars=45)
            answer=st.text_area('💬 Твой ответ',placeholder='Сегодня я узнал(а)… / Мне понравилось… / Я хочу узнать…',max_chars=160,height=135)
            send=st.form_submit_button('🚀 Отправить ответ',type='primary',use_container_width=True)
        if send:
            try: add(name,answer)
            except ValueError as e: st.warning(str(e))
            except sqlite3.Error: st.error('Ошибка сохранения. Попробуй ещё раз.')
            else:
                st.success('🎉 Спасибо! Твой ответ появился на общем экране.');st.balloons()
        st.link_button('👀 Посмотреть общий экран',wall_url,use_container_width=True)
    with right:
        st.markdown('<div class="panel"><b>🌈 Как это работает?</b><p>1. Напиши своё имя.<br>2. Расскажи, что узнал(а), что понравилось или осталось непонятным.<br>3. Нажми «Отправить ответ».</p>💡 Здесь нет неправильных ответов. Главное — твоё мнение!</div>',unsafe_allow_html=True)
        st.markdown('<div class="panel"><b>🔒 Помни о безопасности</b><p>Ответ увидит класс. Не указывай телефон, адрес или другую личную информацию.</p></div>',unsafe_allow_html=True)

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
