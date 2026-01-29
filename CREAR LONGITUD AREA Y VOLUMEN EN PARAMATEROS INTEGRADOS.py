import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

# Colectar todos los elementos de modelo (instancias)
collector = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

opt = Options()
opt.DetailLevel = ViewDetailLevel.Fine
opt.ComputeReferences = True

TransactionManager.Instance.EnsureInTransaction(doc)

contador = 0

for el in collector:
    try:
        geom = el.get_Geometry(opt)
        if not geom: continue
        
        # Variables para almacenar el máximo del elemento actual
        vol_total = 0.0
        max_f_area = 0.0
        max_e_long = 0.0
        tiene_geometria = False

        # Función para analizar cada sólido individualmente
        def analizar_solido(s, v_acc, a_max, l_max):
            if s and s.Volume > 0.0001: # Ignorar sólidos insignificantes
                v_acc += s.Volume
                for face in s.Faces:
                    if face.Area > a_max:
                        a_max = face.Area
                    for loop in face.EdgeLoops:
                        for edge in loop:
                            if edge.ApproximateLength > l_max:
                                l_max = edge.ApproximateLength
                return v_acc, a_max, l_max, True
            return v_acc, a_max, l_max, False

        # Extraer sólidos de la geometría (incluyendo instancias)
        for obj in geom:
            if isinstance(obj, Solid):
                vol_total, max_f_area, max_e_long, tiene_geometria = analizar_solido(obj, vol_total, max_f_area, max_e_long)
            elif isinstance(obj, GeometryInstance):
                for inst_obj in obj.GetInstanceGeometry():
                    if isinstance(inst_obj, Solid):
                        vol_total, max_f_area, max_e_long, tiene_geometria = analizar_solido(inst_obj, vol_total, max_f_area, max_e_long)

        if tiene_geometria:
            # --- GESTIÓN DE UNIDADES ---
            # Si tus parámetros son de tipo "Volumen", "Área" y "Longitud", 
            # Revit espera pies internos (Internal Units). NO multipliques por 0.3048.
            # El sistema hará la conversión automática a metros en la interfaz.
            
            p_vol = el.LookupParameter("VOLUMEN INTEGRADO")
            p_area = el.LookupParameter("AREA INTEGRADO")
            p_long = el.LookupParameter("LONGITUD INTEGRADO")
            
            if p_vol and not p_vol.IsReadOnly:
                p_vol.Set(vol_total)
            if p_area and not p_area.IsReadOnly:
                p_area.Set(max_f_area)
            if p_long and not p_long.IsReadOnly:
                p_long.Set(max_e_long)
                
            contador += 1
    except:
        continue

TransactionManager.Instance.TransactionTaskDone()

OUT = "Se actualizaron {} elementos con éxito.".format(contador)