import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

# Colectar todos los elementos que no sean Tipos (instancias de modelo)
collector = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

opt = Options()
opt.DetailLevel = ViewDetailLevel.Fine
opt.ComputeReferences = True
opt.IncludeNonVisibleObjects = False # Evita líneas ocultas que falsean la longitud

TransactionManager.Instance.EnsureInTransaction(doc)

contador = 0

for el in collector:
    # Saltar elementos sin categoría (como materiales o estilos)
    if el.Category is None: continue
    
    # Solo procesar categorías de modelo comunes
    if el.Category.CategoryType != CategoryType.Model: continue

    try:
        geom = el.get_Geometry(opt)
        if not geom: continue
        
        vol_total = 0.0
        max_f_area = 0.0
        max_e_long = 0.0
        encontrado = False

        # Extraer todos los sólidos, incluso dentro de GeometryInstances
        solidos = []
        for obj in geom:
            if isinstance(obj, Solid):
                solidos.append(obj)
            elif isinstance(obj, GeometryInstance):
                # Importante: GetSymbolGeometry() para familias o GetInstanceGeometry()
                solidos.extend([s for s in obj.GetInstanceGeometry() if isinstance(s, Solid)])

        for s in solidos:
            if s.Volume > 0.000001: # Filtro de precisión
                encontrado = True
                vol_total += s.Volume
                for face in s.Faces:
                    if face.Area > max_f_area: max_f_area = face.Area
                    for loop in face.EdgeLoops:
                        for edge in loop:
                            if edge.ApproximateLength > max_e_long:
                                max_e_long = edge.ApproximateLength

        if encontrado:
            # Intentar escribir en los parámetros si existen
            params = {
                "VOLUMEN INTEGRADO": vol_total,
                "AREA INTEGRADO": max_f_area,
                "LONGITUD INTEGRADO": max_e_long
            }
            
            p_exito = False
            for p_nombre, p_valor in params.items():
                p = el.LookupParameter(p_nombre)
                if p and not p.IsReadOnly:
                    p.Set(p_valor)
                    p_exito = True
            
            if p_exito: contador += 1

    except:
        continue

TransactionManager.Instance.TransactionTaskDone()

OUT = "Listo. Se actualizaron {} elementos del modelo.".format(contador)
