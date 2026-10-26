from __future__ import annotations
import base64, csv, hmac, html, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
import qrcode
from scene import render_scene, effect_settings
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

# Оформление хранится отдельно: меняйте style.css без редактирования Python-кода.
def load_css():
    stylesheet = Path(__file__).with_name('style.css')
    st.markdown('<style>' + stylesheet.read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)


# Визуальный кластер вынесен в scene.py; CSS/JS/JSON находятся рядом с app.py.

def header(label, s):
    st.markdown(f'<div class="brand">📚 {esc(s["school"])} &nbsp;·&nbsp; {esc(label)}</div>',unsafe_allow_html=True)

def wall(student_url):
    s=settings();header('ОБЩИЙ ЭКРАН',s)
    left,right=st.columns([4.6,1.2],gap='large',vertical_alignment='center')
    with left:
        st.markdown(f'<div class="hero"><div class="over">✨ НАШ ШКОЛЬНЫЙ УРОК</div><h1>{esc(s["topic"])} 💭</h1><p>{esc(s["question"])} Поделись мыслью — она появится на нашем общем экране!</p></div>',unsafe_allow_html=True)
    with right:
        qr_base64 = base64.b64encode(qr(student_url)).decode('ascii')
        st.markdown(
            '<div class="qr-panel">'
            '<div class="qr-title"><span class="qr-title-icon">📱</span>'
            '<span>Сканируй и отвечай</span></div>'
            f'<img class="qr-graphic" src="data:image/png;base64,{qr_base64}" '
            'alt="QR-код для ответа на вопрос урока">'
            f'<a class="qr-action" href="{esc(student_url)}">'
            '✍️ Написать ответ</a>'
            '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="kicker">НАША ОБЩАЯ РЕФЛЕКСИЯ</div><div class="heading">Каждая мысль важна 🌟</div>',unsafe_allow_html=True)
    effects = effect_settings()
    @st.fragment(run_every=f"{effects['refresh_seconds']}s")
    def live():
        recent=all_answers(MAX_CARDS)
        ids={int(r['id']) for r in recent};old=st.session_state.get('previous_ids')
        fresh=ids-old if old is not None else set();st.session_state['previous_ids']=ids
        # Публичный экран не показывает количество ответов и технический статус.
        st.markdown('<div class="wall-visual-gap" aria-hidden="true"></div>',
                    unsafe_allow_html=True)
        render_scene(recent, fresh, s['school'], effects=effects)
        if not recent: st.info('✨ Здесь скоро появятся первые ответы!')
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
    init();load_css()
    wall_url,student_url,_=urls()
    view=st.query_params.get('view','wall')
    if view=='student':student(wall_url)
    elif view=='admin':admin(wall_url)
    else:wall(student_url)

if __name__=='__main__':main()
