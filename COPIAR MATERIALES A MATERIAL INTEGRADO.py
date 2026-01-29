import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

# Recolectar TODOS los elementos que no sean tipos y tengan nombre
collector = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

resultados = []

TransactionManager.Instance.EnsureInTransaction(doc)

for e in collector:
    try:
        if e.Category is None: continue
        
        nombre_mat = None
        type_id = e.GetTypeId()
        e_type = doc.GetElement(type_id) if type_id != ElementId.InvalidElementId else None
        
        # ESTRATEGIA 1: Buscar en estructuras compuestas (Muros, Suelos, Techos)
        if e_type and hasattr(e_type, "GetCompoundStructure"):
            comp_struc = e_type.GetCompoundStructure()
            if comp_struc:
                m_id = comp_struc.GetLayers()[0].MaterialId
                if m_id != ElementId.InvalidElementId:
                    nombre_mat = doc.GetElement(m_id).Name

        # ESTRATEGIA 2: Si sigue vacío, buscar parámetro de Material (Columnas, Vigas, Familias cargables)
        if not nombre_mat:
            # Intentamos con parámetros comunes de material
            for p_name in ["Material", "Structural Material", "Material estructural"]:
                p = e.LookupParameter(p_name)
                if p and p.AsElementId() != ElementId.InvalidElementId:
                    nombre_mat = doc.GetElement(p.AsElementId()).Name
                    break

        # ESTRATEGIA 3: Buscar en el Tipo (si no está en la instancia)
        if not nombre_mat and e_type:
            p = e_type.LookupParameter("Material")
            if p and p.AsElementId() != ElementId.InvalidElementId:
                nombre_mat = doc.GetElement(p.AsElementId()).Name

        # ESCRIBIR RESULTADO
        if nombre_mat:
            param_destino = e.LookupParameter("MATERIAL INTEGRADO")
            if param_destino and not param_destino.IsReadOnly:
                param_destino.Set(nombre_mat)
                resultados.append(e.Category.Name + ": " + nombre_mat)
                
    except Exception:
        continue

TransactionManager.Instance.TransactionTaskDone()

OUT = resultados 