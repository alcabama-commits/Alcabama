import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

# 1. Colectar todos los elementos de instancia en el modelo
col = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

# Definiciones
nombres_niveles = ["Nivel de referencia", "Nivel", "Nivel base", "Restricción de base"]
param_nivel_dest = "NIVEL INTEGRADO"
param_mat_dest = "MATERIAL INTEGRADO"

TransactionManager.Instance.EnsureInTransaction(doc)
conteo = 0

def obtener_nivel_texto(elemento):
    """Busca el nivel en un elemento según la lista de prioridades."""
    for n in nombres_niveles:
        p_ori = elemento.LookupParameter(n)
        if p_ori and p_ori.HasValue:
            # Intentar obtener como texto directo (nombre del nivel)
            txt = p_ori.AsValueString()
            if not txt:
                # Si falla, obtener por ID del nivel
                id_n = p_ori.AsElementId()
                if id_n != ElementId.InvalidElementId:
                    obj_n = doc.GetElement(id_n)
                    if obj_n: return obj_n.Name
            else:
                return txt
    return None

for e in col:
    try:
        # Verificar si el elemento tiene los parámetros destino
        p_nivel_out = e.LookupParameter(param_nivel_dest)
        p_mat_out = e.LookupParameter(param_mat_dest)
        
        if not p_nivel_out and not p_mat_out:
            continue

        # --- LÓGICA DE NIVEL ---
        if p_nivel_out and not p_nivel_out.IsReadOnly:
            nivel_final = obtener_nivel_texto(e)
            
            # CASO ESPECIAL: Si es una PIEZA (Part) y no tiene nivel propio
            if not nivel_final and isinstance(e, Part):
                # Obtener los elementos que originaron esta pieza
                parent_ids = e.GetSourceElementIds()
                for p_id in parent_ids:
                    parent_el = doc.GetElement(p_id.ElementId)
                    if parent_el:
                        nivel_final = obtener_nivel_texto(parent_el)
                        if nivel_final: break
            
            if nivel_final:
                p_nivel_out.Set(nivel_final)

        # --- LÓGICA DE MATERIAL (Solo si tiene el parámetro) ---
        if p_mat_out and not p_mat_out.IsReadOnly:
            nombre_mat = "Sin Material"
            # Si es pieza, el material está en el parámetro de instancia 'Material'
            if isinstance(e, Part):
                m_p = e.get_Parameter(BuiltInParameter.DPART_MATERIAL_ID_PARAM)
                if m_p and m_p.HasValue:
                    nombre_mat = doc.GetElement(m_p.AsElementId()).Name
            else:
                # Lógica para Muros/Suelos originales (Compound Structure)
                e_type = doc.GetElement(e.GetTypeId())
                if e_type:
                    comp_struc = e_type.GetCompoundStructure()
                    if comp_struc:
                        m_id = comp_struc.GetLayerMaterialId(comp_struc.GetFirstCoreLayerIndex())
                        if m_id != ElementId.InvalidElementId:
                            nombre_mat = doc.GetElement(m_id).Name
            p_mat_out.Set(nombre_mat)
            
        conteo += 1
    except:
        continue

TransactionManager.Instance.TransactionTaskDone()
OUT = "Éxito. Se procesaron {} elementos (incluyendo Piezas)".format(conteo)

# Salida con el conteo de elementos afectados
OUT = "Proceso completado. Se actualizaron {} elementos.".format(conteo_exitos)
