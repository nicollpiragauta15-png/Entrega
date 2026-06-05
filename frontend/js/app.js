const API_URL = '';
let turnosAsignados = [];
let porterosData = [];
let formularioHabilitado = true;
let ultimoTurno = null;

const fechaInput = document.getElementById('fecha');
const porteroSelect = document.getElementById('portero');
const diaDescansoSelect = document.getElementById('diaDescanso');
const diaAsignarSelect = document.getElementById('diaAsignar');
const horaInicioInput = document.getElementById('horaInicio');
const horaFinInput = document.getElementById('horaFin');
const horasMantenimientoSelect = document.getElementById('horasMantenimiento');
const conteoHorasSpan = document.getElementById('conteoHoras');
const btnAsignar = document.getElementById('btnAsignar');
const alertDiv = document.getElementById('alert');
const tablaAsignaciones = document.getElementById('tablaAsignaciones');
const tablaAsignacionesPersonal = document.getElementById('tablaAsignacionesPersonal');
const btnContinuar = document.getElementById('btnContinuar');
const fechaActualSpan = document.getElementById('fechaActual');
const btnReiniciar = document.getElementById('btnReiniciar');
const tablaContabilidad = document.getElementById('tablaContabilidad');
const modalEditar = document.getElementById('modalEditar');
const formEditar = document.getElementById('formEditar');
const btnExportarExcel = document.getElementById('btnExportarExcel');

function mostrarAlerta(mensaje, tipo) {
    alertDiv.textContent = mensaje;
    alertDiv.className = `alert alert-${tipo}`;
    alertDiv.style.display = 'block';
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 3000);
}

async function cargarPorteros() {
    try {
        const response = await fetch(`${API_URL}/api/porteros`);
        const data = await response.json();
        if (data.success) {
            porterosData = data.data;
            porteroSelect.innerHTML = '<option value="">Seleccione un portero</option>';
            data.data.forEach(portero => {
                porteroSelect.innerHTML += `<option value="${portero.id}">${portero.nombre}</option>`;
            });
            
            // 👇 AGREGAR ESTA LÍNEA 👇
            porteroSelect.disabled = false;
        }
    } catch (error) {
        mostrarAlerta('Error al cargar porteros', 'error');
    }
}

function inicializarDiasSemana() {

    const todosDias = [
        'Lunes',
        'Martes',
        'Miércoles',
        'Jueves',
        'Viernes',
        'Sábado',
        'Domingo'
    ];

    const porteroId = parseInt(porteroSelect.value);
    const portero = porterosData.find(p => p.id === porteroId);

    diaDescansoSelect.innerHTML = '';

    if (!portero) return;

    // Día fijo automático
    diaDescansoSelect.innerHTML = `
        <option value="${portero.dia_descanso}">
            ${portero.dia_descanso}
        </option>
    `;

    diaDescansoSelect.value =
        portero.dia_descanso;

    // Bloquear cambio manual
    diaDescansoSelect.disabled = true;

    // Crear días disponibles
    const diasDisponibles =
        todosDias.filter(
            dia =>
                dia !== portero.dia_descanso
        );

    diaAsignarSelect.innerHTML =
        '<option value="">Seleccione día a asignar</option>';

    diasDisponibles.forEach(dia => {

        diaAsignarSelect.innerHTML += `
            <option value="${dia}">
                ${dia}
            </option>
        `;
    });

    diaAsignarSelect.disabled = false;

    horaInicioInput.disabled = false;

    horaFinInput.disabled = false;
}

function actualizarDiasAsignar() {
    const diaDescanso = diaDescansoSelect.value;
    const todosDias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    const diasDisponibles = todosDias.filter(dia => dia !== diaDescanso);
    
    diaAsignarSelect.innerHTML = '<option value="">Seleccione día a asignar</option>';
    diasDisponibles.forEach(dia => {
        diaAsignarSelect.innerHTML += `<option value="${dia}">${dia}</option>`;
    });
    diaAsignarSelect.disabled = false;
    horaInicioInput.disabled = false;
    horaFinInput.disabled = false;
}

function calcularHoras() {
    const horaInicio = horaInicioInput.value;
    const horaFin = horaFinInput.value;
    const esMantenimiento = horasMantenimientoSelect.value === 'true';
    const limiteHoras = esMantenimiento ? 2 : 8;
    
    console.log("🕐 calcularHoras ejecutado - Hora inicio:", horaInicio, "Hora fin:", horaFin); // 👈 LOG
    
    if (horaInicio && horaFin) {
        const [inicioHoras, inicioMinutos] = horaInicio.split(':').map(Number);
        let [finHoras, finMinutos] = horaFin.split(':').map(Number);
        
        let horas = finHoras - inicioHoras;
        let minutos = finMinutos - inicioMinutos;
        
        if (horas < 0 || (horas === 0 && minutos < 0)) {
            horas += 24;
        }
        
        if (minutos < 0) {
            horas--;
            minutos += 60;
        }
        
        const totalHoras = horas + (minutos / 60);
        conteoHorasSpan.textContent = totalHoras.toFixed(1);
        
        if (totalHoras > limiteHoras) {

            mostrarAlerta(
                `⚠️ Advertencia:
                ${totalHoras.toFixed(1)} horas.
                Supera el límite recomendado
                de ${limiteHoras} horas`,
                'error'
            );

            verificarConflictoConTurnosAnteriores(
                totalHoras
            );

        } else if (totalHoras > 0) {

            verificarConflictoConTurnosAnteriores(
                totalHoras
            );

        } else {

            btnAsignar.disabled = true;
        }
        
        // 👇 LLAMAR A actualizarRecomendacion AQUÍ
        console.log("📢 Llamando a actualizarRecomendacion desde calcularHoras");
        actualizarRecomendacion();
        
    } else {
        conteoHorasSpan.textContent = '0';
        btnAsignar.disabled = true;
    }
}

function verificarConflictoConTurnosAnteriores(totalHoras) {
    const fecha = fechaInput.value;
    const diaAsignar = diaAsignarSelect.value;
    const horaInicio = horaInicioInput.value;
    const horaFin = horaFinInput.value;
    
    // Buscar turnos existentes en la misma fecha y día
    const turnosExistentes = turnosAsignados.filter(t => 
        t.fecha === fecha && t.dia_asignar === diaAsignar
    );
    
    let hayConflicto = false;
    for (let turno of turnosExistentes) {
        const inicioExistente = turno.hora_inicio;
        const finExistente = turno.hora_fin;
        
        // Verificar si los horarios se cruzan
        if (!(horaFin <= inicioExistente || horaInicio >= finExistente)) {
            hayConflicto = true;
            mostrarAlerta(`⚠️ Conflicto horario: Ya existe un turno de ${inicioExistente} a ${finExistente} en este día`, 'error');
            break;
        }
    }
    
    if (!hayConflicto && totalHoras <= 8) {
        btnAsignar.disabled = false;
    } else {
        btnAsignar.disabled = true;
    }
}

async function cargarAsignaciones() {
    const fecha = fechaInput.value;
    if (!fecha) return;
    
    fechaActualSpan.textContent = fecha;
    
    try {
        const response = await fetch(`${API_URL}/api/asignaciones`);
        const data = await response.json();
        
        if (data.success) {
            turnosAsignados = data.data;
            
            if (turnosAsignados.length === 0) {
                tablaAsignaciones.innerHTML = '<div class="empty-table">No hay turnos asignados para esta fecha</div>';
                btnContinuar.style.display = 'none';
            } else {
                let html = `
                    <table class="tabla-turnos">
                        <thead>
                            <tr>
                                <th>Día</th><th>Horario</th><th>Portero</th>
                                <th>Horas</th><th>Actividad</th><th>Fecha Asignación</th>
                                <th>Dia descanso</th><th>Editar</th><th>Eliminar</th>
                            </thead>
                            <tbody>
                `;
                
                turnosAsignados.forEach(turno => {
                    html += `
                        <tr>
                            <td><strong>${turno.dia_asignar}</strong><br><small class="fecha-dia">${formatearFecha(turno.fecha)}</small></td>
                            <td><strong>${turno.hora_inicio} - ${turno.hora_fin}</strong></td>
                            <td>
                                <select onchange="cambiarPortero(${turno.id}, this.value)">
                                    ${porterosData.map(p => `<option value="${p.id}" ${p.id == turno.portero_id ? 'selected' : ''}>${p.nombre}</option>`).join('')}
                                </select>
                            </td>
                            <td><span class="badge ${turno.horas <= 8 ? 'badge-success' : 'badge-warning'}">${turno.horas} horas</span></td>
                            <td>${turno.actividad}</td>
                            <td>${turno.fecha_registro}</td>
                            <td>${turno.dia_descanso}</td>
                            <td><button class="btn-editar" onclick="abrirModalEditar(${turno.id})">✏️</button></td>
                            <td><button class="btn-eliminar" onclick="confirmarEliminar(${turno.id}, '${turno.portero_nombre}', '${turno.dia_asignar}', '${turno.hora_inicio}', '${turno.hora_fin}')">🗑️</button></td>
                        </tr>
                    `;
                });
                
                html += `</tbody></table>`;
                tablaAsignaciones.innerHTML = html;
                actualizarContabilidadPersonal();
                btnContinuar.style.display = 'block';
            }
            
            // 👇 ACTUALIZAR PREVIEW DESPUÉS DE CADA CAMBIO
            await actualizarPreviewExcel();
        }
    } catch (error) {
        console.error('Error al cargar asignaciones:', error);
        mostrarAlerta('Error al cargar asignaciones', 'error');
    }
}

// Función para confirmar eliminación
function confirmarEliminar(id, porteroNombre, dia, horaInicio, horaFin) {
    const confirmacion = confirm(
        `¿Estás seguro de que deseas eliminar este turno?\n\n` +
        `Portero: ${porteroNombre}\n` +
        `Día: ${dia}\n` +
        `Horario: ${horaInicio} - ${horaFin}\n\n` +
        `Esta acción no se puede deshacer.`
    );
    
    if (confirmacion) {
        eliminarTurno(id);
    }
}

// Función para eliminar el turno
async function eliminarTurno(asignacionId) {
    try {
        const response = await fetch(`${API_URL}/api/eliminar-turno/${asignacionId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            mostrarAlerta(resultado.message, 'success');
            await cargarAsignaciones();
            await actualizarPreviewExcel();
        } else {
            mostrarAlerta(resultado.message, 'error');
        }
    } catch (error) {
        console.error('Error al eliminar turno:', error);
        mostrarAlerta('Error al eliminar el turno', 'error');
    }
}

function actualizarContabilidadPersonal() {

    if (turnosAsignados.length === 0) {

        tablaContabilidad.innerHTML =
            '<div class="empty-table">No hay datos del personal</div>';

        return;
    }

    const contabilidad = {};

    // Recorrer TODOS los turnos guardados
    turnosAsignados.forEach(turno => {

        const nombre = turno.portero_nombre;

        if (!contabilidad[nombre]) {

            contabilidad[nombre] = {
                horas: 0,
                turnos: 0
            };
        }

        contabilidad[nombre].horas += turno.horas;
        contabilidad[nombre].turnos += 1;
    });

    let html = `
        <table>
            <thead>
                <tr>
                    <th>Portero</th>
                    <th>Total Horas</th>
                    <th>Total Turnos</th>
                    <th>Estado</th>
                </tr>
            </thead>

            <tbody>
    `;

    Object.keys(contabilidad).forEach(nombre => {

        const datos = contabilidad[nombre];

        let estado = 'Disponible';
        let clase = 'badge-success';

        if (datos.horas >= 42) {

            estado = 'Alta carga';
            clase = 'badge-warning';
        }

        if (datos.horas >= 44) {

            estado = 'Límite excedido';
            clase = 'badge-warning';
        }

        html += `
            <tr>

                <td>
                    ${nombre}
                </td>

                <td>
                    <strong>
                        ${datos.horas.toFixed(1)} horas
                    </strong>
                </td>

                <td>
                    ${datos.turnos}
                </td>

                <td>
                    <span class="badge ${clase}">
                        ${estado}
                    </span>
                </td>

            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    tablaContabilidad.innerHTML = html;
}


function habilitarFormularioParaNuevoTurno() {
    // Limpiar campos
    diaDescansoSelect.innerHTML = '';
    diaAsignarSelect.innerHTML = '<option value="">Primero seleccione día de descanso</option>';
    diaAsignarSelect.disabled = true;
    horaInicioInput.value = '';
    horaFinInput.value = '';
    horaInicioInput.disabled = true;
    horaFinInput.disabled = true;
    conteoHorasSpan.textContent = '0';
    btnAsignar.disabled = true;
    
    // Habilitar campos necesarios
    diaDescansoSelect.disabled = true;
    porteroSelect.disabled = false;
    fechaInput.disabled = false;
    
    mostrarAlerta('✨ Puede continuar asignando turnos. Recuerde que no pueden cruzar horarios', 'success');
}

async function asignarTurno(event) {
    event.preventDefault();
    
    const data = {
        fecha: fechaInput.value,
        portero_id: parseInt(porteroSelect.value),

        dia_descanso: (
            diaDescansoSelect.value ||
            diaDescansoSelect.options[
                diaDescansoSelect.selectedIndex
            ]?.value
        ),

        dia_asignar: diaAsignarSelect.value,
        hora_inicio: horaInicioInput.value,
        hora_fin: horaFinInput.value,
        horas_mantenimiento:
            horasMantenimientoSelect.value === 'true'
                ? 'Si'
                : 'No'
    };
    
    if (!data.fecha ||!data.portero_id ||!data.dia_asignar ||!data.hora_inicio ||!data.hora_fin) {
        mostrarAlerta('Por favor complete todos los campos', 'error');
        return;
    }
    
    if (data.dia_asignar === data.dia_descanso) {
        mostrarAlerta('El día de descanso no puede ser igual al día de asignación', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/asignar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            mostrarAlerta(resultado.message, 'success');
            await cargarAsignaciones();
            
            // Limpiar campos específicos para nuevo turno
            diaDescansoSelect.innerHTML = '';
            diaAsignarSelect.innerHTML = '<option value="">Primero seleccione día de descanso</option>';
            diaAsignarSelect.disabled = true;
            horaInicioInput.value = '';
            horaFinInput.value = '';
            horaInicioInput.disabled = true;
            horaFinInput.disabled = true;
            conteoHorasSpan.textContent = '0';
            btnAsignar.disabled = true;
            
            // Mantener el portero seleccionado pero habilitar día de descanso
            diaDescansoSelect.disabled = true;
        } else {
            mostrarAlerta(resultado.message, 'error');
        }
    } catch (error) {
        mostrarAlerta('Error al asignar turno', 'error');
    }
}

async function eliminarTurno(asignacionId) {
    try {
        const response = await fetch(`${API_URL}/api/eliminar-turno/${asignacionId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const resultado = await response.json();
        
        if (resultado.success) {
            mostrarAlerta(resultado.message, 'success');
            await cargarAsignaciones();
            await actualizarPreviewExcel();
        } else {
            mostrarAlerta(resultado.message, 'error');
        }
    } catch (error) {
        console.error('Error al eliminar turno:', error);
        mostrarAlerta('Error al eliminar el turno', 'error');
    }
}


// Event Listeners
porteroSelect.addEventListener('change', () => {
    if (porteroSelect.value) {
        inicializarDiasSemana();
    } else {
        diaDescansoSelect.disabled = true;
    }
});



function convertirHora24h(horaConAmPm) {
    if (!horaConAmPm) return horaConAmPm;
    
    // Si ya está en formato 24h, devolver igual
    if (!horaConAmPm.includes('AM') && !horaConAmPm.includes('PM')) {
        return horaConAmPm;
    }
    
    let [hora, minuto, periodo] = horaConAmPm.split(/[:\s]/);
    hora = parseInt(hora);
    minuto = parseInt(minuto);
    
    if (periodo === 'PM' && hora !== 12) {
        hora += 12;
    } else if (periodo === 'AM' && hora === 12) {
        hora = 0;
    }
    
    return `${hora.toString().padStart(2, '0')}:${minuto.toString().padStart(2, '0')}`;
}





let recomendacionActual = null;

async function actualizarRecomendacion() {

    const fecha = fechaInput.value;
    const horaInicio = horaInicioInput.value;

    if (!fecha || !horaInicio) return;

    try {

        const response = await fetch('/api/recomendacion', {

            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                fecha: fecha,
                hora_inicio: horaInicio,
                portero_id: parseInt(porteroSelect.value),
                dia_descanso:diaDescansoSelect.value,
                mantenimiento:horasMantenimientoSelect.value === 'true'
            })
        });

        const data = await response.json();

        if (data.success) {
            recomendacionActual = data.data;
            document.getElementById('label-recomendacion').innerText =`Recomendación:
                ${data.data.hora_inicio}
                - ${data.data.hora_fin}
                (${data.data.horas_turno} horas)`;
        }
    } catch (error) {
        console.error('Error recomendación:',error);
    }
}

function usarRecomendacion() {

    if (!recomendacionActual) return;

    // Activar campo hora fin
    document.getElementById('horaFin').disabled = false;

    // Asignar hora fin
    document.getElementById('horaFin').value =
        recomendacionActual.hora_fin;

    // Mostrar horas
    document.getElementById('conteoHoras').innerText =
        recomendacionActual.horas_turno;

    // Habilitar botón
    document.getElementById('btnAsignar').disabled = false;
}

async function reiniciarRegistros() {
    const confirmar = confirm('¿Seguro que desea eliminar todos los registros?');
    if (!confirmar) return;
    
    try {
        const response = await fetch('/api/reiniciar', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            turnosAsignados = [];
            tablaAsignaciones.innerHTML = '<div class="empty-table">No hay turnos asignados para esta fecha</div>';
            tablaContabilidad.innerHTML = '<div class="empty-table">No hay datos del personal</div>';
            document.getElementById('formAsignacion').reset();
            conteoHorasSpan.textContent = '0';
            diaDescansoSelect.disabled = true;
            diaAsignarSelect.disabled = true;
            horaInicioInput.disabled = true;
            horaFinInput.disabled = true;
            btnAsignar.disabled = true;
            btnContinuar.style.display = 'none';
            
            // 👇 Actualizar preview después de reiniciar
            await actualizarPreviewExcel();
            
            mostrarAlerta('🗑️ Registros eliminados correctamente', 'success');
        } else {
            mostrarAlerta(data.message, 'error');
        }
    } catch (error) {
        mostrarAlerta('Error al reiniciar registros', 'error');
    }
}


async function cambiarPortero(asignacionId, nuevoPorteroId) {
    const response = await fetch('/api/modificar-portero', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asignacion_id: asignacionId, nuevo_portero_id: nuevoPorteroId })
    });
    
    const data = await response.json();
    mostrarAlerta(data.message, data.success ? 'success' : 'error');
    
    if (data.success) {
        await cargarAsignaciones();
        await actualizarPreviewExcel();
    }
}

function abrirModalEditar(id) {
    const turno = turnosAsignados.find(
        t => t.id === id
    );

    if (!turno) return;
    modalEditar.style.display = 'flex';
    document.getElementById('editarId').value =
        turno.id;

    // Porteros
    const selectPortero =
        document.getElementById(
            'editarPortero'
        );

    selectPortero.innerHTML = '';

    porterosData.forEach(portero => {

        selectPortero.innerHTML += `
            <option
                value="${portero.id}"
                ${portero.id == turno.portero_id
                    ? 'selected'
                    : ''}
            >
                ${portero.nombre}
            </option>
        `;
    });

    // Dias
    const dias = [
        'Lunes',
        'Martes',
        'Miércoles',
        'Jueves',
        'Viernes',
        'Sábado',
        'Domingo'
    ];

    const selectDia =
        document.getElementById(
            'editarDia'
        );

    selectDia.innerHTML = '';

    dias.forEach(dia => {

        selectDia.innerHTML += `
            <option
                value="${dia}"
                ${dia === turno.dia_asignar
                    ? 'selected'
                    : ''}
            >
                ${dia}
            </option>
        `;
    });

    document.getElementById('editarHoraInicio').value = turno.hora_inicio;
    document.getElementById('editarHoraFin').value = turno.hora_fin;
    document.getElementById('editarActividad').value = turno.actividad;
}

function cerrarModalEditar() {

    modalEditar.style.display = 'none';
}


if (formEditar) {
    formEditar.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            id: document.getElementById('editarId').value,
            portero_id: document.getElementById('editarPortero').value,
            dia_asignar: document.getElementById('editarDia').value,
            hora_inicio: document.getElementById('editarHoraInicio').value,
            hora_fin: document.getElementById('editarHoraFin').value,
            actividad: document.getElementById('editarActividad').value
        };
        
        const response = await fetch('/api/editar-turno', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const resultado = await response.json();
        mostrarAlerta(resultado.message, resultado.success ? 'success' : 'error');
        
        if (resultado.success) {
            cerrarModalEditar();
            await cargarAsignaciones();
            await actualizarPreviewExcel();
        }
    });
}

async function actualizarPreviewExcel() {
    const previewDiv = document.getElementById('excelPreview');
    if (!previewDiv) return;
    
    try {
        previewDiv.innerHTML = '<div class="loading-preview"><i class="fas fa-spinner fa-spin"></i> Generando vista previa...</div>';
        
        const response = await fetch(`${API_URL}/api/excel-preview`);
        const data = await response.json();
        
        if (data.success && data.html) {
            previewDiv.innerHTML = data.html;
        } else {
            previewDiv.innerHTML = '<div class="empty-preview"><i class="fas fa-chart-simple"></i> No hay datos para mostrar</div>';
        }
    } catch (error) {
        console.error('Error al generar preview:', error);
        previewDiv.innerHTML = '<div class="error-preview"><i class="fas fa-exclamation-triangle"></i> Error al cargar la vista previa</div>';
    }
}

function descargarExcel() {
    window.open(`${API_URL}/api/exportar-excel`, '_blank');
}

horaInicioInput.addEventListener('input', calcularHoras);
horaInicioInput.addEventListener('change',actualizarRecomendacion);
horaFinInput.addEventListener('input', calcularHoras);
horasMantenimientoSelect.addEventListener('change',actualizarRecomendacion);
fechaInput.addEventListener('change', cargarAsignaciones);
btnContinuar.addEventListener('click', habilitarFormularioParaNuevoTurno);
document.getElementById('formAsignacion').addEventListener('submit', asignarTurno);
btnReiniciar.addEventListener('click', reiniciarRegistros);
window.abrirModalEditar = abrirModalEditar;
window.cerrarModalEditar = cerrarModalEditar;
btnDescargarExcel.addEventListener('click', descargarExcel);
fechaInput.value = new Date().toISOString().split('T')[0];
cargarPorteros();
cargarAsignaciones();

function formatearFecha(fechaString) {
    if (!fechaString) return '';  
    // Cortamos los primeros 10 caracteres (YYYY-MM-DD)
    const fechaPura = fechaString.split(' ')[0]; 
    const partes = fechaPura.split('-'); // [ "2026", "06", "01" ]
    if (partes.length !== 3) return fechaString;
    // Reorganizamos a formato Latinoamericano: DD/MM/AAAA
    return `${partes[2]}/${partes[1]}/${partes[0]}`;
}


// Inicializar
fechaInput.value = new Date().toISOString().split('T')[0];
cargarPorteros();
cargarAsignaciones();