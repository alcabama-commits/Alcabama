import clr

# Importar Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# Importar DocumentManager y TransactionManager
clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

# 1. Obtener todos los elementos del modelo que no sean tipos
col = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

# 2. Lista de parámetros en orden de prioridad
nombres_busqueda = ["Nivel de referencia", "Nivel", "Nivel base", "Restricción de base"]
parametro_destino = "NIVEL INTEGRADO"

TransactionManager.Instance.EnsureInTransaction(doc)

conteo_exitos = 0

for el in col:
    # Solo procesar elementos que tengan el parámetro destino
    p_dest = el.LookupParameter(parametro_destino)
    
    if p_dest and not p_dest.IsReadOnly:
        valor_encontrado = None
        
        # 3. Buscar el primer parámetro que coincida y tenga valor
        for nombre in nombres_busqueda:
            p_origen = el.LookupParameter(nombre)
            
            if p_origen and p_origen.HasValue:
                # Intentamos obtener el valor como texto (Nombre del nivel)
                valor_encontrado = p_origen.AsValueString()
                
                # Si AsValueString falla (a veces pasa en ciertos parámetros), 
                # intentamos obtener el nombre a través del ElementId
                if not valor_encontrado:
                    id_nivel = p_origen.AsElementId()
                    if id_nivel and id_nivel != ElementId.InvalidElementId:
                        nivel_obj = doc.GetElement(id_nivel)
                        if nivel_obj:
                            valor_encontrado = nivel_obj.Name
                
                if valor_encontrado:
                    break
        
        # 4. Escribir el valor en NIVEL INTEGRADO
        if valor_encontrado:
            try:
                p_dest.Set(valor_encontrado)
                conteo_exitos += 1
            except:
                continue

TransactionManager.Instance.TransactionTaskDone()

# Salida con el conteo de elementos afectados
OUT = "Proceso completado. Se actualizaron {} elementos.".format(conteo_exitos)
