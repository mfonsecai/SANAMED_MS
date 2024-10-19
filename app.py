import re
from datetime import datetime,date
from flask import Flask, render_template, request, session, redirect, url_for, jsonify,flash
from flask_mysqldb import MySQL
import random


# Configurar la aplicación Flask
app = Flask(__name__, template_folder="templates")
app.secret_key = "sanamed"


# Configurar la conexión a la base de datos MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed"
mysql = MySQL(app)


# Función para validar la contraseña
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[!@#$%^&*()_+=\[{\]};:<>|./?,-]", password):
        return False
    return True


# Función para obtener el ID del usuario actualmente logueado
def obtener_id_usuario_actual():
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None


# Función para generar un ID de profesional aleatorio
def generar_id_profesional_aleatorio():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    if profesionales:
        id_profesional = random.choice(profesionales)[0]
        return id_profesional
    else:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "POST" and "correo" in request.form and "contrasena" in request.form:
        username = request.form['correo']
        password = request.form['contrasena']
        rol = request.form['rol']
       
        cur = mysql.connection.cursor()
       
        # Buscar en la tabla de usuarios
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s AND contrasena = %s AND tipo_perfil = %s", (username, password, rol))
        user_data = cur.fetchone()
       
        # Si no se encuentra en la tabla de usuarios, buscar en la tabla de profesionales
        if not user_data and rol == "profesional":
            cur.execute("SELECT id_profesional FROM Profesionales WHERE correo = %s AND contrasena = %s", (username, password))
            user_data = cur.fetchone()
       
        # Si aún no se encuentra, buscar en la tabla de administradores
        if not user_data and rol == "admin":
            cur.execute("SELECT id_administrador FROM Administradores WHERE correo = %s AND contrasena = %s", (username, password))
            user_data = cur.fetchone()


        cur.close()


        if user_data:
            session['logged_in'] = True
            session['id_usuario'] = user_data[0]  # Establecer el ID de usuario en la sesión


            if rol == 'usuario':
                return redirect(url_for('user_home'))
            elif rol == 'profesional':
                return redirect(url_for('profesional_home'))
            elif rol == 'admin':
                return redirect(url_for('admin_home'))
        else:
            return render_template('index.html', error="Credenciales incorrectas")


    return render_template('index.html')






@app.route('/registro_emocion', methods=['POST'])
def registro_emocion():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            # Obtener la emoción seleccionada por el usuario
            emocion = request.form['emocion']


            # Obtener el ID del usuario actualmente logueado
            print("Contenido de la sesión:", session)  # Agregar esta impresión
            id_usuario = obtener_id_usuario_actual()


            # Obtener la fecha y hora actual
            fecha_emocion = datetime.now()


            # Insertar la emoción en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO Emociones (id_usuario, fecha_emocion, emocion) VALUES (%s, %s, %s)",
                        (id_usuario, fecha_emocion, emocion))
            mysql.connection.commit()
            cur.close()


            # Redirigir al usuario de nuevo a la página de inicio
            return redirect(url_for('user_home'))
    else:
        return redirect(url_for('index'))
   
   
@app.route('/signup', methods=["GET", 'POST'])
def register():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        celular = request.form['celular']
        correo = request.form['correo']
        contrasena = request.form['contrasena']


        # Validar la contraseña
        if not validate_password(contrasena):
            flash("La contraseña debe tener al menos 8 caracteres, una mayúscula y un carácter especial.", "error")
            return render_template('register.html')


        # Verificar si el correo electrónico ya está registrado
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s", (correo,))
        existing_user = cur.fetchone()
        cur.close()


        if existing_user:
            flash("El correo electrónico ya está registrado. Por favor, utiliza otro correo electrónico", "error")
            return render_template('register.html')


        # Insertar el nuevo usuario en la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO Usuarios (nombre, tipo_documento, numero_documento, celular, correo, contrasena) VALUES (%s, %s, %s, %s, %s, %s)",
                (nombre, tipo_documento, numero_documento, celular, correo, contrasena))
            mysql.connection.commit()
            flash("Registro exitoso. Inicia sesión con tus credenciales.", "success")
            return redirect(url_for('register'))
        except Exception as e:
            mysql.connection.rollback()
            error = "El número de documento ya se encuentra registrado"
            flash(error, "error")
            return render_template('register.html', error=error)
        finally:
            cur.close()


    return render_template('register.html')


@app.route('/user_home')
def user_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('user_home.html')
    else:
        return redirect(url_for('index'))
   
@app.route('/admin_home')
def admin_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('admin_home.html')
    else:
        return redirect(url_for('index'))
   
@app.route('/profesional_home')
def profesional_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('profesional_home.html')
    else:
        return redirect(url_for('index'))


@app.route('/games')
def games():
    return render_template('games.html')


@app.route('/rompecabezas')
def rompecabezas():
    return render_template('rompecabezas.html')


@app.route('/laberinto')
def laberinto():
    return render_template('laberinto.html')




# Función para obtener un ID de profesional aleatorio
# Función para obtener profesionales disponibles
def obtener_profesionales_disponibles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional, nombre, especialidad FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    return profesionales


@app.route('/agendar_cita', methods=["GET", "POST"])
def agendar_cita():
    if 'logged_in' in session and session['logged_in']:
        if request.method == "POST":
            fecha = request.form['fecha']
            hora = request.form['hora']
            motivo = request.form['motivo']
            id_usuario = session['id_usuario']


            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM Consultas WHERE fecha_consulta = %s AND hora_consulta = %s", (fecha, hora))
            cita_existente = cur.fetchone()
            cur.close()


            # Validar que la fecha no sea anterior a la fecha actual
            fecha_actual = date.today()
            fecha_seleccionada = datetime.strptime(fecha, '%Y-%m-%d').date()


            if fecha_seleccionada < fecha_actual:
                error = "No puedes programar una cita en una fecha anterior a la fecha actual."
                return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())


            if cita_existente:
                error = "Ya hay una cita programada para esa fecha y hora."
                return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())
            else:
                # Convertir la hora AM/PM a un formato de 24 horas
                hora_seleccionada = datetime.strptime(hora, '%I:%M %p').strftime('%H:%M')


                hora_inicio = datetime.strptime('08:00', '%H:%M').time()
                hora_fin = datetime.strptime('17:00', '%H:%M').time()
               
                if hora_seleccionada < hora_inicio.strftime('%H:%M') or hora_seleccionada > hora_fin.strftime('%H:%M'):
                    error = "La hora seleccionada está fuera del rango permitido (8:00 - 17:00)."
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())


                id_profesional = request.form['profesional']


                cur = mysql.connection.cursor()
                try:
                    cur.execute("INSERT INTO Consultas (id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo) VALUES (%s, %s, %s, %s, %s)",
                                (id_usuario, id_profesional, fecha, hora_seleccionada, motivo))
                    mysql.connection.commit()


                    cur.execute("INSERT INTO Profesionales_Usuarios (id_profesional, id_usuario) VALUES (%s, %s)",
                                (id_profesional, id_usuario))
                    mysql.connection.commit()
                except Exception as e:
                    mysql.connection.rollback()
                    error = "Error al programar la cita: " + str(e)
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())
                finally:
                    cur.close()
                # Agregar el mensaje de éxito
                success_message = "Su cita se ha registrado con éxito."
                return render_template('agendar_cita.html', success=success_message, profesionales=obtener_profesionales_disponibles())
    else:
        return redirect(url_for('index'))


    return render_template('agendar_cita.html', profesionales=obtener_profesionales_disponibles())
@app.route('/calendario')
def mostrar_calendario():
    # Aquí debes implementar la lógica para mostrar el calendario
    return render_template('calendario.html')


def obtener_emociones_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT emocion, HOUR(fecha_emocion), MINUTE(fecha_emocion) FROM Emociones WHERE DATE(fecha_emocion) = %s"
    cur.execute(query, (fecha,))
    emociones = []
    horas = []
    for row in cur.fetchall():
        emociones.append(row[0])
        hora = str(row[1]).zfill(2)
        minuto = str(row[2]).zfill(2)
        hora_formateada = f"{hora}:{minuto}"
        horas.append(hora_formateada)
    cur.close()
    return emociones, horas
def obtener_especialidad_profesional(id_profesional):
    cur = mysql.connection.cursor()
    cur.execute("SELECT especialidad FROM Profesionales WHERE id_profesional = %s", (id_profesional,))
    especialidad_profesional = cur.fetchone()[0]
    cur.close()
    return especialidad_profesional


def obtener_consultas_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo FROM Consultas WHERE DATE(fecha_consulta) = %s"
    cur.execute(query, (fecha,))
    consultas = cur.fetchall()
    cur.close()
    return consultas


def obtener_nombre_profesional(id_profesional):
    cur = mysql.connection.cursor()
    cur.execute("SELECT nombre FROM Profesionales WHERE id_profesional = %s", (id_profesional,))
    nombre_profesional = cur.fetchone()[0]
    cur.close()
    return nombre_profesional
@app.route('/seleccionar_dia', methods=['POST'])
def seleccionar_dia():
    if request.method == 'POST':
        fecha_seleccionada = request.form['fecha']
        emociones, horas = obtener_emociones_por_fecha(fecha_seleccionada)
        if not emociones:
            mensaje = "No hay emociones registradas para este día."
            return render_template('calendario.html', mensaje=mensaje)
        return render_template('emociones.html', fecha_seleccionada=fecha_seleccionada, emociones_horas=zip(emociones, horas))


@app.route('/consultas_dia', methods=["GET", 'POST'])
def consultas_dia():
    if request.method == 'POST':
        fecha_seleccionada = request.form['fecha']
        consultas = obtener_consultas_por_fecha(fecha_seleccionada)
        if not consultas:
            mensaje = "No hay citas registradas para este día."
            return render_template('calendario.html', mensaje=mensaje)
        return render_template('consultas.html', fecha_seleccionada=fecha_seleccionada, consultas=consultas, obtener_nombre_profesional=obtener_nombre_profesional, obtener_especialidad_profesional=obtener_especialidad_profesional)
@app.route('/profesionales')
def listar_profesionales():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional, nombre, especialidad FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    return render_template('lista_profesionales.html', profesionales=profesionales)


@app.route('/agregar_profesional', methods=["GET", "POST"])
def agregar_profesional():
    if request.method == "POST":
        nombre = request.form['nombre']
        especialidad = request.form['especialidad']
        correo = request.form['correo']
        contrasena = request.form['contrasena']


        # Validación de la contraseña
        if not validate_password(contrasena):
            error = "La contraseña debe tener al menos 8 caracteres, incluyendo letras, números y caracteres especiales."
            return render_template('agregar_profesional.html', error=error)


        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO Profesionales (nombre, especialidad, correo, contrasena) VALUES (%s, %s, %s, %s)",
                        (nombre, especialidad, correo, contrasena))
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            error = "Error al agregar profesional: " + str(e)
            return render_template('agregar_profesional.html', error=error)
        finally:
            cur.close()
        return redirect(url_for('listar_profesionales'))
    return render_template('agregar_profesional.html')


@app.route('/eliminar_profesional/<int:id>', methods=["POST"])
def eliminar_profesional(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM Profesionales WHERE id_profesional=%s", (id,))
        mysql.connection.commit()
        flash("Profesional eliminado correctamente", "success")
    except Exception as e:
        mysql.connection.rollback()
        error = "Error al eliminar profesional "
        flash(error, "error")
    finally:
        cur.close()


    return redirect(url_for('listar_profesionales'))


@app.route('/usuarios')
def listar_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_usuario, numero_documento, correo FROM Usuarios")
    usuarios = cur.fetchall()  # Cambio de nombre de la variable para reflejar que son usuarios, no profesionales
    cur.close()
    return render_template('lista_usuarios.html', usuarios=usuarios)  # Cambio de la plantilla a lista_usuarios.html
@app.route('/eliminar_usuario/<int:id>', methods=["POST"])
def eliminar_usuario(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM Usuarios WHERE id_usuario=%s", (id,))
        mysql.connection.commit()
        flash('Usuario eliminado correctamente', 'success')  # Mensaje de éxito
    except Exception as e:
        mysql.connection.rollback()
        error = "Error al eliminar usuario "
        flash(error, 'error')  # Mensaje de error
    finally:
        cur.close()
    return redirect(url_for('listar_usuarios'))


@app.route('/citas_agendadas')
def listar_citas():
    cur = mysql.connection.cursor()
   
    query = """
    SELECT
        u.numero_documento,
        p.nombre AS nombre_profesional,
        c.fecha_consulta,
        c.hora_consulta,
        c.motivo,
        c.id_consulta
    FROM
        Consultas c
    JOIN
        Usuarios u ON c.id_usuario = u.id_usuario
    LEFT JOIN
        Profesionales p ON c.id_profesional = p.id_profesional;
    """
   
    cur.execute(query)
    citas = cur.fetchall()
    cur.close()
   
    return render_template('lista_consultas.html', citas=citas)
@app.route('/eliminar_cita/<int:id>', methods=['POST'])
def eliminar_cita(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Consultas WHERE id_consulta = %s", (id,))
    mysql.connection.commit()
    cur.close()
   
    # Emitir un mensaje flash después de eliminar la cita con éxito
    flash('La cita ha sido eliminada correctamente.', 'success')
   
    return redirect(url_for('listar_citas'))


@app.route('/pacientes')
def pacientes():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()
       
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT  u.nombre,  u.numero_documento, u.celular, u.correo
            FROM Usuarios u
            JOIN profesionales_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE pu.id_profesional = %s
        """, (id_profesional,))
       
        pacientes = cur.fetchall()
        cur.close()
       
        return render_template('lista_pacientes.html', pacientes=pacientes)
    else:
        return redirect(url_for('index'))


@app.route('/citas_asignadas')
def citas_asignadas():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()
       
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT c.id_consulta, u.nombre AS nombre_paciente, u.numero_documento, u.correo AS correo_paciente, c.fecha_consulta, c.hora_consulta, c.motivo
            FROM Consultas c
            JOIN Usuarios u ON c.id_usuario = u.id_usuario
            WHERE c.id_profesional = %s
        """, (id_profesional,))
       
        citas = cur.fetchall()
        cur.close()
       
        return render_template('citas_asignadas.html', citas=citas)
    else:
        return redirect(url_for('index'))
class Consulta:
    def __init__(self, id_consulta, numero_documento, fecha_consulta, hora_consulta, motivo, diagnostico, tratamiento):
        self.id_consulta = id_consulta
        self.numero_documento = numero_documento
        self.fecha_consulta = fecha_consulta
        self.hora_consulta = hora_consulta
        self.motivo = motivo
        self.diagnostico = diagnostico
        self.tratamiento = tratamiento
@app.route('/diagnosticos_tratamientos', methods=['GET', 'POST'])
def diagnosticos_tratamientos():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()  # Obtener el ID del profesional logueado


        cur = mysql.connection.cursor()
        cur.execute("""
    SELECT DISTINCT c.id_consulta, u.numero_documento, c.fecha_consulta, c.hora_consulta, c.motivo, c.diagnostico, c.tratamiento
    FROM Consultas c
    JOIN Usuarios u ON c.id_usuario = u.id_usuario
    JOIN Profesionales_Usuarios pu ON c.id_profesional = pu.id_profesional
    WHERE c.fecha_consulta < %s AND pu.id_profesional = %s
""", (datetime.now(), id_profesional))


        consultas = cur.fetchall()
        cur.close()


        consultas_obj = [Consulta(*consulta) for consulta in consultas]


        if request.method == 'POST':
            flash('Actualizado correctamente', 'success')


        return render_template('diagnosticos_tratamientos.html', consultas=consultas_obj)
    else:
        return redirect(url_for('index'))
@app.route('/editar_diagnostico_tratamiento/<int:id_consulta>', methods=['POST'])
def editar_diagnostico_tratamiento(id_consulta):
    diagnostico = request.form['diagnostico']
    tratamiento = request.form['tratamiento']
   
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE Consultas
        SET diagnostico = %s, tratamiento = %s
        WHERE id_consulta = %s
    """, (diagnostico, tratamiento, id_consulta))
    mysql.connection.commit()
    cur.close()
   
    flash('El diagnóstico y tratamiento se han actualizado correctamente.')
    return redirect(url_for('diagnosticos_tratamientos'))


@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html')
@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'logged_in' in session and session['logged_in']:
        id_usuario = obtener_id_usuario_actual()
        cur = mysql.connection.cursor()


        if request.method == 'POST':
            nombre = request.form['nombre']
            numero_documento = request.form['numero_documento']
            celular = request.form['celular']
            correo = request.form['correo']


            cur.execute("""
                UPDATE Usuarios
                SET nombre = %s, numero_documento = %s, celular = %s, correo = %s
                WHERE id_usuario = %s
            """, (nombre, numero_documento, celular, correo, id_usuario))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('configuracion'))


        cur.execute("SELECT nombre, numero_documento, celular, correo FROM Usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario = cur.fetchone()
        cur.close()
        return render_template('editar_perfil.html', usuario=usuario)
    else:
        return redirect(url_for('index'))


@app.route('/sobre_nosotros')
def sobre_nosotros():
    return render_template('sobre_nosotros.html')


@app.route('/preguntas_frecuentes')
def preguntas_frecuentes():
    return render_template('preguntas_frecuentes.html')


if __name__ == '__main__':
    app.secret_key = "sanamed"
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)





