"""Build original synthetic store data without a model or network connection."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORE_ID = "nexo-demo"
GENERATOR_ID = "ragml-demo-data-v1"


def definition(key, label, value_type="text", unit=None, required=False):
    return {
        "key": key,
        "label": label,
        "value_type": value_type,
        "unit": unit,
        "required_for_comparison": required,
        "choices": [],
    }


# Product specifications are invented for this exercise, not copied from manufacturers.
# Tuple fields: name, simulated base price in COP, purpose, attributes.
CATEGORIES = [
    {
        "id": "peripherals",
        "code": "PER",
        "name": "Periféricos",
        "guidance": "Compare primero el tipo de dispositivo y la conexión. Una conexión USB no implica compatibilidad con todos los sistemas operativos. La ficha debe respaldar cada compatibilidad.",
        "definitions": [
            definition("device_type", "Tipo de dispositivo", required=True),
            definition("connection", "Conexión", required=True),
            definition("os_support", "Sistemas documentados", required=True),
            definition("width_cm", "Ancho", "number", "cm"),
            definition("keyboard_layout", "Distribución del teclado"),
            definition("microphone", "Micrófono integrado", "boolean"),
        ],
        "items": [
            (
                "Teclado Brisa",
                89000,
                "Escritura cotidiana en un escritorio pequeño.",
                {
                    "device_type": "teclado",
                    "connection": "Bluetooth 5.0",
                    "os_support": "Windows 11 y Android 13",
                    "width_cm": 29,
                    "keyboard_layout": "español",
                    "microphone": False,
                },
            ),
            (
                "Teclado Pulso",
                179000,
                "Escritura con teclado mecánico y conexión por cable.",
                {
                    "device_type": "teclado",
                    "connection": "USB-A por cable",
                    "os_support": "Windows 11",
                    "width_cm": 36,
                    "keyboard_layout": "español",
                    "microphone": False,
                },
            ),
            (
                "Ratón Arco",
                69000,
                "Uso de oficina con agarre de tamaño mediano.",
                {
                    "device_type": "ratón",
                    "connection": "Bluetooth 5.0",
                    "os_support": "Windows 11 y macOS 14",
                    "width_cm": 7,
                    "microphone": False,
                },
            ),
            (
                "Ratón Viaje",
                39000,
                "Transporte frecuente y uso con receptor incluido.",
                {
                    "device_type": "ratón",
                    "connection": "receptor USB-A de 2,4 GHz",
                    "os_support": "Windows 11",
                    "width_cm": 5.5,
                    "microphone": False,
                },
            ),
            (
                "Auriculares Voz",
                119000,
                "Conversaciones de escritorio con micrófono integrado.",
                {
                    "device_type": "auriculares",
                    "connection": "USB-A por cable",
                    "os_support": "Windows 11 y macOS 14",
                    "width_cm": 17,
                    "microphone": True,
                },
            ),
            (
                "Auriculares Diálogo",
                79000,
                "Llamadas con un dispositivo que tenga conector de audio combinado.",
                {
                    "device_type": "auriculares",
                    "connection": "audio combinado de 3,5 mm",
                    "os_support": "depende del conector de audio combinado del equipo",
                    "width_cm": 16,
                    "microphone": True,
                },
            ),
            (
                "Cámara Encuentro",
                139000,
                "Videollamadas con resolución de prueba de 1080p.",
                {
                    "device_type": "cámara web",
                    "connection": "USB-A por cable",
                    "os_support": "Windows 11",
                    "width_cm": 8,
                    "microphone": True,
                },
            ),
            (
                "Panel Tacto",
                169000,
                "Control del puntero con una superficie táctil externa.",
                {
                    "device_type": "panel táctil",
                    "connection": "Bluetooth 5.0",
                    "os_support": "Windows 11",
                    "width_cm": 12,
                    "microphone": False,
                },
            ),
            (
                "Teclado Cifra",
                59000,
                "Ingreso numérico con un accesorio independiente.",
                {
                    "device_type": "teclado numérico",
                    "connection": "USB-A por cable",
                    "os_support": "Windows 11",
                    "width_cm": 9,
                    "keyboard_layout": "numérica",
                    "microphone": False,
                },
            ),
            (
                "Control Presenta",
                99000,
                "Control de diapositivas mediante un receptor incluido.",
                {
                    "device_type": "control de presentaciones",
                    "connection": "receptor USB-A de 2,4 GHz",
                    "os_support": "Windows 11",
                    "width_cm": 3,
                    "microphone": False,
                },
            ),
        ],
    },
    {
        "id": "connectivity",
        "code": "CON",
        "name": "Conectividad",
        "guidance": "Distinga la forma del conector de sus capacidades. Para video por USB-C debe existir respaldo explícito del modo de video requerido en el equipo y del adaptador. No deduzca video, carga o velocidad por el nombre del puerto.",
        "definitions": [
            definition("device_type", "Tipo de accesorio", required=True),
            definition("host_connector", "Conector del equipo", required=True),
            definition("interfaces", "Interfaces documentadas", required=True),
            definition("power_requirement", "Alimentación"),
            definition("video_output", "Transporta video", "boolean"),
            definition("requires_usb_c_alt_mode", "Requiere modo alternativo USB-C", "boolean"),
        ],
        "items": [
            (
                "Hub Enlace Cuatro",
                79000,
                "Ampliar puertos USB sin salida de video.",
                {
                    "device_type": "hub",
                    "host_connector": "USB-C",
                    "interfaces": "cuatro puertos USB-A de datos",
                    "power_requirement": "alimentación desde el equipo",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Hub Enlace Video",
                169000,
                "Conectar una pantalla cuando el equipo documenta video por USB-C.",
                {
                    "device_type": "hub",
                    "host_connector": "USB-C",
                    "interfaces": "HDMI hasta 3840 x 2160 a 30 Hz y dos USB-A",
                    "power_requirement": "alimentación desde el equipo",
                    "video_output": True,
                    "requires_usb_c_alt_mode": True,
                },
            ),
            (
                "Adaptador Red Clara",
                89000,
                "Conectar por Ethernet un equipo con USB-C de datos.",
                {
                    "device_type": "adaptador de red",
                    "host_connector": "USB-C",
                    "interfaces": "Ethernet hasta 1000 Mbit/s",
                    "power_requirement": "alimentación desde el equipo",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Adaptador Aire",
                59000,
                "Añadir conectividad inalámbrica al equipo de prueba compatible.",
                {
                    "device_type": "adaptador inalámbrico",
                    "host_connector": "USB-A",
                    "interfaces": "Wi-Fi de 2,4 y 5 GHz; Windows 11 documentado",
                    "power_requirement": "alimentación desde el equipo",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Router Doble Ruta",
                229000,
                "Distribuir una conexión de red en el escenario doméstico ficticio.",
                {
                    "device_type": "router",
                    "host_connector": "Ethernet RJ45",
                    "interfaces": "Wi-Fi de 2,4 y 5 GHz; puertos Ethernet de 1000 Mbit/s",
                    "power_requirement": "adaptador incluido",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Extensor Alcance",
                119000,
                "Extender una red inalámbrica en un escenario controlado sin prometer cobertura real.",
                {
                    "device_type": "extensor de red",
                    "host_connector": "Wi-Fi",
                    "interfaces": "Wi-Fi de 2,4 GHz",
                    "power_requirement": "conexión a toma eléctrica",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Cable Carga Sesenta",
                39000,
                "Carga de prueba hasta 60 W sin transporte de video.",
                {
                    "device_type": "cable",
                    "host_connector": "USB-C",
                    "interfaces": "USB-C a USB-C; carga hasta 60 W; longitud 1 m",
                    "power_requirement": "cargador compatible no incluido",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Cable Pantalla Dos",
                49000,
                "Conectar dos puertos HDMI compatibles con el modo de video descrito.",
                {
                    "device_type": "cable",
                    "host_connector": "HDMI",
                    "interfaces": "HDMI a HDMI; longitud 2 m; hasta 3840 x 2160 a 60 Hz",
                    "power_requirement": "sin alimentación externa",
                    "video_output": True,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Distribuidor Red Cinco",
                129000,
                "Conectar hasta cinco enlaces Ethernet en la red de demostración.",
                {
                    "device_type": "switch de red",
                    "host_connector": "Ethernet RJ45",
                    "interfaces": "cinco puertos Ethernet de 1000 Mbit/s",
                    "power_requirement": "adaptador incluido",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
            (
                "Lector Memoria",
                69000,
                "Leer tarjetas SD y microSD mediante USB-C.",
                {
                    "device_type": "lector de tarjetas",
                    "host_connector": "USB-C",
                    "interfaces": "SD y microSD; no incluye tarjetas",
                    "power_requirement": "alimentación desde el equipo",
                    "video_output": False,
                    "requires_usb_c_alt_mode": False,
                },
            ),
        ],
    },
    {
        "id": "lighting",
        "code": "ILU",
        "name": "Iluminación",
        "guidance": "Compare alimentación, potencia, altura, regulación y temperatura de color. Todos los artículos de esta categoría se describen para interiores secos; no existe una certificación de uso exterior en estas fuentes ficticias.",
        "definitions": [
            definition("power_w", "Potencia", "number", "W", True),
            definition("power_source", "Alimentación", required=True),
            definition("color_temperature", "Temperatura de color", required=True),
            definition("dimmable", "Intensidad regulable", "boolean"),
            definition("height_cm", "Altura", "number", "cm"),
            definition("use_location", "Lugar de uso"),
        ],
        "items": [
            (
                "Lámpara Flexo",
                89000,
                "Iluminar un escritorio con brazo ajustable.",
                {
                    "power_w": 8,
                    "power_source": "adaptador incluido",
                    "color_temperature": "3000, 4000 y 6000 K",
                    "dimmable": True,
                    "height_cm": 40,
                    "use_location": "interior seco",
                },
            ),
            (
                "Lámpara Pinza",
                59000,
                "Iluminar una superficie con borde apto para una pinza de hasta 4 cm.",
                {
                    "power_w": 5,
                    "power_source": "USB-A de 5 V; adaptador no incluido",
                    "color_temperature": "4000 K",
                    "dimmable": True,
                    "height_cm": 32,
                    "use_location": "interior seco",
                },
            ),
            (
                "Barra Monitor",
                149000,
                "Iluminar la mesa desde la parte superior de un monitor de prueba.",
                {
                    "power_w": 5,
                    "power_source": "USB-A de 5 V; adaptador no incluido",
                    "color_temperature": "3000, 4000 y 6000 K",
                    "dimmable": True,
                    "height_cm": 3,
                    "use_location": "interior seco",
                },
            ),
            (
                "Tira Ambiente",
                49000,
                "Aportar iluminación ambiental en una longitud de 2 m.",
                {
                    "power_w": 10,
                    "power_source": "adaptador incluido",
                    "color_temperature": "3000 K",
                    "dimmable": False,
                    "height_cm": 0.3,
                    "use_location": "interior seco",
                },
            ),
            (
                "Aro Encuadre",
                119000,
                "Iluminar una videollamada desde una base de mesa.",
                {
                    "power_w": 10,
                    "power_source": "USB-A de 5 V; adaptador no incluido",
                    "color_temperature": "3000, 4000 y 6000 K",
                    "dimmable": True,
                    "height_cm": 45,
                    "use_location": "interior seco",
                },
            ),
            (
                "Lámpara Pie Suave",
                229000,
                "Iluminación ambiental de pie con luz cálida.",
                {
                    "power_w": 12,
                    "power_source": "adaptador incluido",
                    "color_temperature": "3000 K",
                    "dimmable": True,
                    "height_cm": 145,
                    "use_location": "interior seco",
                },
            ),
            (
                "Luz Armario",
                39000,
                "Iluminación de un compartimento con batería recargable.",
                {
                    "power_w": 3,
                    "power_source": "batería recargable por USB-C; cable incluido",
                    "color_temperature": "4000 K",
                    "dimmable": False,
                    "height_cm": 2,
                    "use_location": "interior seco",
                },
            ),
            (
                "Luz Lectura",
                29000,
                "Iluminar una zona de lectura con accesorio compacto.",
                {
                    "power_w": 2,
                    "power_source": "dos pilas AAA no incluidas",
                    "color_temperature": "3000 K",
                    "dimmable": False,
                    "height_cm": 18,
                    "use_location": "interior seco",
                },
            ),
            (
                "Lámpara Base Carga",
                179000,
                "Iluminación con una base de carga cuya compatibilidad debe comprobarse por separado.",
                {
                    "power_w": 15,
                    "power_source": "adaptador incluido",
                    "color_temperature": "3000, 4000 y 6000 K",
                    "dimmable": True,
                    "height_cm": 38,
                    "use_location": "interior seco",
                },
            ),
            (
                "Luz Noche",
                25000,
                "Iluminación cálida de orientación, sin promesa de cobertura de una habitación.",
                {
                    "power_w": 1,
                    "power_source": "conexión a toma eléctrica",
                    "color_temperature": "2700 K",
                    "dimmable": False,
                    "height_cm": 8,
                    "use_location": "interior seco",
                },
            ),
        ],
    },
    {
        "id": "organization",
        "code": "ORG",
        "name": "Organización",
        "guidance": "Compare dimensiones, material, instalación y carga documentada. Un producto que cabe por ancho puede no caber por profundidad o altura. No deduzca cargas máximas cuando no estén disponibles.",
        "definitions": [
            definition("material", "Material", required=True),
            definition("width_cm", "Ancho", "number", "cm", True),
            definition("depth_cm", "Profundidad", "number", "cm", True),
            definition("height_cm", "Altura", "number", "cm", True),
            definition("installation", "Instalación"),
            definition("max_load_kg", "Carga máxima", "number", "kg"),
        ],
        "items": [
            (
                "Organizador Tres",
                19000,
                "Separar útiles en tres compartimentos de mesa.",
                {
                    "material": "plástico",
                    "width_cm": 18,
                    "depth_cm": 10,
                    "height_cm": 10,
                    "installation": "sobre superficie",
                    "max_load_kg": 1,
                },
            ),
            (
                "Caja Cables",
                29000,
                "Agrupar cables dejando libres las aberturas de ventilación.",
                {
                    "material": "plástico",
                    "width_cm": 30,
                    "depth_cm": 12,
                    "height_cm": 12,
                    "installation": "sobre superficie",
                    "max_load_kg": 1,
                },
            ),
            (
                "Elevador Monitor",
                89000,
                "Elevar un monitor dentro de las dimensiones y carga publicadas.",
                {
                    "material": "madera laminada",
                    "width_cm": 50,
                    "depth_cm": 22,
                    "height_cm": 12,
                    "installation": "sobre superficie",
                    "max_load_kg": 10,
                },
            ),
            (
                "Soporte Portátil",
                69000,
                "Elevar un portátil con base de hasta 30 cm de ancho.",
                {
                    "material": "aluminio",
                    "width_cm": 30,
                    "depth_cm": 25,
                    "height_cm": 15,
                    "installation": "sobre superficie",
                    "max_load_kg": 5,
                },
            ),
            (
                "Cajonera Módulo",
                109000,
                "Ordenar documentos en tres cajones de sobremesa.",
                {
                    "material": "plástico",
                    "width_cm": 28,
                    "depth_cm": 35,
                    "height_cm": 30,
                    "installation": "sobre superficie",
                    "max_load_kg": 6,
                },
            ),
            (
                "Repisa Liviana",
                69000,
                "Organizar objetos con fijación mural apropiada para la pared.",
                {
                    "material": "madera laminada",
                    "width_cm": 60,
                    "depth_cm": 18,
                    "height_cm": 2,
                    "installation": "fijación a pared; idoneidad de pared no evaluada",
                    "max_load_kg": 5,
                },
            ),
            (
                "Panel Orden",
                129000,
                "Colgar accesorios ligeros en un panel de organización.",
                {
                    "material": "acero",
                    "width_cm": 50,
                    "depth_cm": 2,
                    "height_cm": 35,
                    "installation": "fijación a pared; idoneidad de pared no evaluada",
                    "max_load_kg": 4,
                },
            ),
            (
                "Cesta Trama",
                24000,
                "Almacenar objetos pequeños en una cesta abierta.",
                {
                    "material": "tela",
                    "width_cm": 25,
                    "depth_cm": 20,
                    "height_cm": 15,
                    "installation": "sobre superficie",
                    "max_load_kg": 2,
                },
            ),
            (
                "Archivo Vertical",
                39000,
                "Separar carpetas en posición vertical.",
                {
                    "material": "cartón rígido",
                    "width_cm": 24,
                    "depth_cm": 26,
                    "height_cm": 30,
                    "installation": "sobre superficie",
                    "max_load_kg": 3,
                },
            ),
            (
                "Sujetacables Seis",
                15000,
                "Sujetar seis cables finos sin soportar objetos suspendidos.",
                {
                    "material": "silicona",
                    "width_cm": 12,
                    "depth_cm": 2,
                    "height_cm": 1,
                    "installation": "adhesivo para superficie lisa",
                    "max_load_kg": None,
                },
            ),
        ],
    },
    {
        "id": "furniture",
        "code": "MOB",
        "name": "Mobiliario",
        "guidance": "Compare el tipo de mueble y las medidas completas antes de recomendarlo. La carga máxima documentada no demuestra beneficios médicos ni una ergonomía individual. Un atributo desconocido impide confirmar ese requisito.",
        "definitions": [
            definition("furniture_type", "Tipo de mueble", required=True),
            definition("material", "Material"),
            definition("width_cm", "Ancho", "number", "cm", True),
            definition("depth_cm", "Profundidad", "number", "cm", True),
            definition("height_cm", "Altura nominal", "number", "cm", True),
            definition("adjustable", "Dispone de ajuste", "boolean"),
            definition("max_load_kg", "Carga máxima", "number", "kg", True),
        ],
        "items": [
            (
                "Escritorio Plano",
                499000,
                "Trabajo de escritorio con una superficie de 120 por 60 cm.",
                {
                    "furniture_type": "escritorio",
                    "material": "madera laminada y acero",
                    "width_cm": 120,
                    "depth_cm": 60,
                    "height_cm": 75,
                    "adjustable": False,
                    "max_load_kg": 50,
                },
            ),
            (
                "Escritorio Compacto",
                329000,
                "Trabajo en un espacio con ancho limitado a 80 cm.",
                {
                    "furniture_type": "escritorio",
                    "material": "madera laminada y acero",
                    "width_cm": 80,
                    "depth_cm": 45,
                    "height_cm": 75,
                    "adjustable": False,
                    "max_load_kg": 30,
                },
            ),
            (
                "Escritorio Ascenso",
                1599000,
                "Alternar altura mediante ajuste manual entre 72 y 110 cm.",
                {
                    "furniture_type": "escritorio",
                    "material": "madera laminada y acero",
                    "width_cm": 120,
                    "depth_cm": 60,
                    "height_cm": 72,
                    "adjustable": True,
                    "max_load_kg": 40,
                },
            ),
            (
                "Escritorio Esquina",
                999000,
                "Ubicación en esquina con una superficie de 140 por 100 cm.",
                {
                    "furniture_type": "escritorio",
                    "material": "madera laminada y acero",
                    "width_cm": 140,
                    "depth_cm": 100,
                    "height_cm": 75,
                    "adjustable": False,
                    "max_load_kg": 50,
                },
            ),
            (
                "Silla Base",
                329000,
                "Asiento de oficina con altura regulable de 88 a 100 cm.",
                {
                    "furniture_type": "silla",
                    "material": "tela y acero",
                    "width_cm": 55,
                    "depth_cm": 55,
                    "height_cm": 88,
                    "adjustable": True,
                    "max_load_kg": 100,
                },
            ),
            (
                "Silla Malla",
                649000,
                "Asiento con respaldo de malla y altura regulable de 95 a 107 cm.",
                {
                    "furniture_type": "silla",
                    "material": "malla y acero",
                    "width_cm": 62,
                    "depth_cm": 60,
                    "height_cm": 95,
                    "adjustable": True,
                    "max_load_kg": 120,
                },
            ),
            (
                "Silla Compacta",
                459000,
                "Asiento de dimensiones reducidas y altura regulable de 85 a 97 cm.",
                {
                    "furniture_type": "silla",
                    "material": "tela y acero",
                    "width_cm": 50,
                    "depth_cm": 50,
                    "height_cm": 85,
                    "adjustable": True,
                    "max_load_kg": 90,
                },
            ),
            (
                "Estante Abierto",
                299000,
                "Almacenamiento abierto con cuatro niveles.",
                {
                    "furniture_type": "estante",
                    "material": "madera laminada",
                    "width_cm": 60,
                    "depth_cm": 30,
                    "height_cm": 140,
                    "adjustable": False,
                    "max_load_kg": 40,
                },
            ),
            (
                "Carro Auxiliar",
                189000,
                "Trasladar objetos ligeros entre superficies de trabajo.",
                {
                    "furniture_type": "carro auxiliar",
                    "material": "acero",
                    "width_cm": 40,
                    "depth_cm": 30,
                    "height_cm": 70,
                    "adjustable": False,
                    "max_load_kg": 15,
                },
            ),
            (
                "Reposapiés Apoyo",
                89000,
                "Apoyar los pies sin utilizar el accesorio como asiento.",
                {
                    "furniture_type": "reposapiés",
                    "material": "plástico",
                    "width_cm": 40,
                    "depth_cm": 30,
                    "height_cm": 12,
                    "adjustable": True,
                    "max_load_kg": None,
                },
            ),
        ],
    },
    {
        "id": "everyday-accessories",
        "code": "ACC",
        "name": "Accesorios cotidianos",
        "guidance": "Compare tipo de accesorio, material, medidas, capacidad y cuidados. No intercambie mililitros y litros sin conversión explícita. No afirme conservación térmica, impermeabilidad o aptitud alimentaria que la ficha no documente.",
        "definitions": [
            definition("accessory_type", "Tipo de accesorio", required=True),
            definition("material", "Material", required=True),
            definition("capacity_ml", "Capacidad de recipiente", "number", "ml"),
            definition("capacity_l", "Capacidad de bolsa", "number", "L"),
            definition("width_cm", "Ancho", "number", "cm"),
            definition("care", "Cuidados"),
        ],
        "items": [
            (
                "Botella Ruta",
                39000,
                "Transportar 500 ml de bebida en el escenario ficticio.",
                {
                    "accessory_type": "botella",
                    "material": "acero inoxidable",
                    "capacity_ml": 500,
                    "width_cm": 7,
                    "care": "lavado manual; no usar en microondas",
                },
            ),
            (
                "Botella Aislada",
                79000,
                "Transportar 750 ml sin una duración térmica certificada.",
                {
                    "accessory_type": "botella",
                    "material": "acero inoxidable de doble pared",
                    "capacity_ml": 750,
                    "width_cm": 8,
                    "care": "lavado manual; no usar en microondas",
                },
            ),
            (
                "Taza Mesa",
                29000,
                "Recipiente de escritorio con capacidad de 350 ml.",
                {
                    "accessory_type": "taza",
                    "material": "cerámica",
                    "capacity_ml": 350,
                    "width_cm": 9,
                    "care": "lavado manual; compatibilidad con microondas no documentada",
                },
            ),
            (
                "Vaso Trayecto",
                59000,
                "Transportar hasta 450 ml con tapa sin afirmar cierre hermético.",
                {
                    "accessory_type": "vaso con tapa",
                    "material": "acero inoxidable",
                    "capacity_ml": 450,
                    "width_cm": 8,
                    "care": "lavado manual; mantener vertical",
                },
            ),
            (
                "Bolsa Almuerzo",
                49000,
                "Organizar recipientes con volumen exterior nominal de 4 L.",
                {
                    "accessory_type": "bolsa",
                    "material": "poliéster",
                    "capacity_l": 4,
                    "width_cm": 24,
                    "care": "limpieza con paño húmedo; aislamiento térmico no medido",
                },
            ),
            (
                "Mochila Jornada",
                129000,
                "Transportar objetos cotidianos con capacidad nominal de 15 L.",
                {
                    "accessory_type": "mochila",
                    "material": "poliéster",
                    "capacity_l": 15,
                    "width_cm": 28,
                    "care": "limpieza manual; impermeabilidad no documentada",
                },
            ),
            (
                "Estuche Conexiones",
                59000,
                "Ordenar cables y adaptadores en compartimentos interiores.",
                {
                    "accessory_type": "estuche",
                    "material": "poliéster",
                    "width_cm": 22,
                    "care": "limpieza con paño húmedo",
                },
            ),
            (
                "Bolsa Reutiliza",
                24000,
                "Transportar objetos ligeros en una bolsa de tela abierta.",
                {
                    "accessory_type": "bolsa",
                    "material": "algodón",
                    "capacity_l": 10,
                    "width_cm": 35,
                    "care": "lavado manual en agua fría",
                },
            ),
            (
                "Tapete Escritorio",
                49000,
                "Cubrir una superficie de trabajo de 60 por 30 cm.",
                {
                    "accessory_type": "tapete",
                    "material": "corcho y caucho",
                    "width_cm": 60,
                    "care": "paño húmedo; no sumergir",
                },
            ),
            (
                "Kit Paño",
                19000,
                "Retirar polvo con un paño de microfibra sin químicos incluidos.",
                {
                    "accessory_type": "limpieza",
                    "material": "microfibra",
                    "width_cm": 20,
                    "care": "lavar el paño separado; seguir las indicaciones del equipo a limpiar",
                },
            ),
        ],
    },
]

POLICIES = [
    (
        "prices",
        "Precios de demostración",
        "Los precios son importes finales simulados en COP. El registro comercial de la variante es la fuente de su precio; una ficha o una guía no confirma un importe vigente. No hay descuentos implícitos. Precio desconocido no significa precio cero. El envío se consulta en la política de entrega y no se presupone incluido en un presupuesto de producto.",
    ),
    (
        "availability",
        "Disponibilidad de demostración",
        "Las existencias se consultan por variante. Cero unidades significa agotado; valor desconocido no significa disponibilidad. Una disponibilidad explícita puede existir sin cantidad exacta. Consultar no reserva inventario. Precio y existencias caducan por separado; una lectura no renueva su fecha de actualización. Los datos vencidos no deben confirmarse como actuales.",
    ),
    (
        "delivery",
        "Entrega de demostración",
        "En la zona ficticia de cobertura, el plazo orientativo es de tres a cinco días hábiles. El costo simulado es de 15 000 COP y será cero desde un subtotal de productos de 300 000 COP. No se ha definido una dirección real ni se realizan despachos. Si el usuario exige un presupuesto total con envío, se debe distinguir el subtotal del costo simulado de entrega y aclarar la cobertura.",
    ),
    (
        "exchanges",
        "Cambios de demostración",
        "El escenario permite consultar solicitudes dentro de los 15 días siguientes a la entrega ficticia, con producto sin uso y comprobante simulado. El asistente explica la condición, pero no procesa solicitudes, devoluciones ni reembolsos. No se afirma la existencia de una compra particular ni se pide información de pago.",
    ),
    (
        "warranty",
        "Garantía de demostración",
        "La garantía ficticia cubre defectos de fabricación durante 12 meses y excluye daños por uso indebido. Las particularidades requieren respaldo en la ficha del producto. El asistente no decide reclamaciones ni promete su aceptación. Este texto es una regla inventada para pruebas y no describe derechos legales ni condiciones de una empresa real.",
    ),
    (
        "help",
        "Ayuda de demostración",
        "Ante información insuficiente o contradictoria, el asistente debe explicarlo, pedir una aclaración útil o indicar que se consulte un canal humano cuando exista uno configurado. Nexo Demo no tiene empleados, correo ni canal humano conectado. El asistente no debe inventar datos de contacto ni afirmar que envió un mensaje. La tienda, los productos y sus condiciones son ficticios.",
    ),
]

SYNTHETIC_WEIGHTS_G = {
    "peripherals": [350, 720, 95, 65, 230, 180, 120, 140, 110, None],
    "connectivity": [85, 150, 45, 15, 420, 180, 55, 140, 250, None],
    "lighting": [550, 280, 450, 130, 780, 2500, 120, 60, 1100, None],
    "organization": [180, 420, 1800, 650, 1600, 850, 1400, 200, 450, None],
    "furniture": [18000, 12000, 28000, 24000, 9500, 14000, 10500, 16000, 6000, None],
    "everyday-accessories": [250, 420, 330, 300, 180, 550, 150, 100, 650, None],
}


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def timestamp(value):
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def display(value):
    if value is None:
        return "No disponible en la fuente"
    if isinstance(value, bool):
        return "Sí" if value else "No"
    return str(value)


def build_package(as_of, revision, output_relative):
    files = {}
    sources, chunks, products, variants, snapshots, categories = [], [], [], [], [], []
    coverage = []

    def add_source(source_id, title, scope_kind, target_id, relative, sections):
        banner = (
            "Datos sintéticos originales de Nexo Demo. No representan una oferta comercial real."
        )
        content = f"# {title}\n\n{banner}\n\nFuente: {source_id}. Versión: {revision}.\n\n"
        blocks = [f"## {heading}\n\n{text}" for heading, text in sections]
        content += "\n\n".join(blocks) + "\n"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        files[relative] = content
        sources.append(
            {
                "store_id": STORE_ID,
                "source_id": source_id,
                "title": title,
                "version": revision,
                "content_hash": digest,
                "data_mode": "demo",
                "scope": {"kind": scope_kind, "target_id": target_id},
                "locator": f"{output_relative}/{relative}",
                "provenance": "synthetic_created",
                "active": True,
            }
        )
        for number, ((heading, _), block) in enumerate(zip(sections, blocks, strict=True), 1):
            if len(block) > 4000:
                raise ValueError(f"Chunk too long: {source_id}/{number}")
            chunks.append(
                {
                    "store_id": STORE_ID,
                    "chunk_id": f"{source_id}-s{number}",
                    "source_id": source_id,
                    "source_version": revision,
                    "source_content_hash": digest,
                    "content_hash": hashlib.sha256(block.encode("utf-8")).hexdigest(),
                    "text": block,
                    "location": {"section": heading},
                }
            )

    for category in CATEGORIES:
        definitions = category["definitions"] + [definition("weight_g", "Masa", "number", "g")]
        categories.append(
            {
                "category_id": category["id"],
                "name": category["name"],
                "attribute_definitions": definitions,
            }
        )
        definition_map = {item["key"]: item for item in definitions}
        for number, (name, base_price, purpose, supplied) in enumerate(category["items"], 1):
            product_id = f"NEX-{category['code']}-{number:03d}"
            source_id = f"doc-{category['code'].lower()}-{number:03d}"
            attrs = dict(supplied)
            attrs["weight_g"] = SYNTHETIC_WEIGHTS_G[category["id"]][number - 1]
            product_attrs = [
                {
                    "key": key,
                    "value": value,
                    "unit": definition_map[key]["unit"],
                    "evidence_refs": [source_id] if value is not None else [],
                }
                for key, value in attrs.items()
            ]
            products.append(
                {
                    "store_id": STORE_ID,
                    "product_id": product_id,
                    "category_id": category["id"],
                    "name": name,
                    "attributes": product_attrs,
                    "revision": revision,
                }
            )
            product_variants = []
            for index, label in enumerate(
                ["Presentación A", "Presentación B"] if number <= 5 else ["Única"]
            ):
                variant_id = f"{product_id}-{index + 1:02d}"
                variants.append(
                    {
                        "store_id": STORE_ID,
                        "variant_id": variant_id,
                        "product_id": product_id,
                        "name": label,
                        "attributes": [],
                        "revision": revision,
                        "sku": f"DEMO-{category['code']}-{number:03d}-{index + 1:02d}",
                    }
                )
                product_variants.append(
                    f"- {variant_id}: {label}. Conserva los atributos comunes; tiene registro comercial propio."
                )
                price_time = as_of - timedelta(minutes=30) if number == 10 else as_of
                quantity = 0 if number == 7 else 2 + number + index
                stock_value = (
                    None
                    if number == 9
                    else {
                        "availability": "out_of_stock" if quantity == 0 else "in_stock",
                        "quantity": None if number == 6 else quantity,
                    }
                )
                price_value = (
                    None
                    if number == 8
                    else {
                        "amount": str(base_price + index * 5000),
                        "currency": "COP",
                    }
                )
                snapshots.append(
                    {
                        "store_id": STORE_ID,
                        "variant_id": variant_id,
                        "snapshot_id": f"{revision}-{variant_id}",
                        "source_id": "commercial-nexo-demo",
                        "revision": revision,
                        "price": {
                            "value": price_value,
                            "source_updated_at": timestamp(price_time),
                            "expires_at": timestamp(price_time + timedelta(minutes=15)),
                            "source_ref": f"commercial-nexo-demo#{variant_id}/price",
                        },
                        "stock": {
                            "value": stock_value,
                            "source_updated_at": timestamp(as_of),
                            "expires_at": timestamp(as_of + timedelta(minutes=15)),
                            "source_ref": f"commercial-nexo-demo#{variant_id}/stock",
                        },
                    }
                )
            attribute_lines = [
                f"- {definition_map[key]['label']} ({key}): {display(value)}"
                + (
                    f" {definition_map[key]['unit']}"
                    if value is not None and definition_map[key]["unit"]
                    else ""
                )
                + "."
                for key, value in attrs.items()
            ]
            presentation_note = (
                "Las presentaciones A y B son opciones ficticias de empaque; no cambian las características documentadas. "
                if number <= 5
                else "Este producto solo tiene la presentación única enumerada en esta ficha. "
            )
            context = f"Producto {product_id}, {name}. Categoría: {category['name']}. Datos de demostración."
            add_source(
                source_id,
                f"Ficha de {name}",
                "product",
                product_id,
                f"documents/products/{product_id.lower()}.md",
                [
                    (
                        "Resumen",
                        f"{context}\n\n{purpose} Las capacidades y medidas son inventadas para este ejercicio.",
                    ),
                    ("Características", context + "\n\n" + "\n".join(attribute_lines)),
                    (
                        "Variantes y límites",
                        context
                        + "\n\n"
                        + "\n".join(product_variants)
                        + "\n\n"
                        + presentation_note
                        + "Precios y existencias se consultan en el registro estructurado de cada variante. "
                        + "No se afirman otras compatibilidades ni prestaciones. La garantía general ficticia se consulta en su política.",
                    ),
                ],
            )
        add_source(
            f"guide-{category['id']}",
            f"Guía de {category['name']}",
            "category",
            category["id"],
            f"documents/guides/{category['id']}.md",
            [
                (
                    "Criterios de selección",
                    f"Categoría de demostración: {category['name']}. {category['guidance']}",
                ),
                (
                    "Preguntas y límites",
                    "Antes de recomendar, confirme necesidad, presupuesto y requisitos obligatorios. "
                    "La categoría no sustituye al tipo de artículo: dos productos de una categoría pueden tener usos distintos. "
                    "Consulte la ficha y la variante exactas. Un dato no disponible exige aclaración o abstención. "
                    "Los precios, el stock y sus fechas proceden del registro comercial, no de esta guía.",
                ),
            ],
        )
        coverage.append(
            {
                "category_id": category["id"],
                "products": 10,
                "variants": 15,
                "product_sources": 10,
                "guide_sources": 1,
            }
        )

    for policy_id, title, body in POLICIES:
        add_source(
            f"policy-{policy_id}",
            title,
            "store",
            None,
            f"documents/policies/{policy_id}.md",
            [
                ("Condiciones", body),
                (
                    "Naturaleza de la fuente",
                    "Esta es una política ficticia creada para pruebas académicas. "
                    "No acredita derechos legales, una empresa existente ni operaciones comerciales. "
                    "Debe sustituirse por documentación autorizada al integrar una tienda real.",
                ),
            ],
        )

    catalog = {
        "schema_version": "0.1",
        "profile": {
            "schema_version": "0.1",
            "store_id": STORE_ID,
            "display_name": "Nexo Demo",
            "data_mode": "demo",
            "locale": "es-CO",
            "currency": "COP",
            "currency_decimal_places": 0,
            "categories": categories,
            "revision": revision,
            "human_contact": None,
        },
        "products": products,
        "variants": variants,
    }
    files["catalog.json"] = json_text(catalog)
    files["commercial.json"] = json_text(
        {
            "schema_version": "0.1",
            "store_id": STORE_ID,
            "data_mode": "demo",
            "revision": revision,
            "snapshots": snapshots,
        }
    )
    files["sources.json"] = json_text(
        {
            "schema_version": "0.1",
            "store_id": STORE_ID,
            "data_mode": "demo",
            "revision": revision,
            "sources": sources,
            "chunks": chunks,
        }
    )
    files["package-metadata.json"] = json_text(
        {
            "generated_by": GENERATOR_ID,
            "store_id": STORE_ID,
            "data_mode": "demo",
            "revision": revision,
            "synthetic_observation_time": timestamp(as_of),
            "recommended_test_time": timestamp(as_of + timedelta(minutes=5)),
            "commercial_ttl_seconds": 900,
            "counts": {
                "categories": 6,
                "products": 60,
                "variants": 90,
                "commercial_records": len(snapshots),
                "sources": len(sources),
                "chunks": len(chunks),
            },
            "coverage": coverage,
            "provenance": "Original invented specifications; no real store, manufacturer or participant data.",
            "intentional_conditions": {
                "product_06_each_category": "Availability known, exact quantity unknown",
                "product_07_each_category": "Out of stock",
                "product_08_each_category": "Price unknown",
                "product_09_each_category": "Stock unknown",
                "product_10_each_category": "Price stale at recommended test time; mass unknown",
            },
            "integration_status": "Prepared data, sources and section chunks; no retrieval index or final evaluation.",
            "file_hashes": {
                name: hashlib.sha256(value.encode("utf-8")).hexdigest()
                for name, value in sorted(files.items())
            },
        }
    )
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of", required=True, help="Synthetic observation time with explicit timezone"
    )
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", default="data/sample")
    parser.add_argument(
        "--check", action="store_true", help="Compare expected bytes without writing files"
    )
    parser.add_argument(
        "--replace-generated",
        action="store_true",
        help="Explicitly replace this generator's previous package",
    )
    args = parser.parse_args()
    try:
        as_of = datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
        if as_of.utcoffset() is None:
            raise ValueError("--as-of requires an explicit timezone")
        if not args.revision.strip():
            raise ValueError("--revision cannot be empty")
        output = (PROJECT_ROOT / args.output).resolve()
        if not output.is_relative_to(PROJECT_ROOT / "data") or output == PROJECT_ROOT / "data":
            raise ValueError("Output must be a child directory of the project's data directory")
        files = build_package(as_of, args.revision, output.relative_to(PROJECT_ROOT).as_posix())
        if args.check:
            mismatches = [
                name
                for name, value in files.items()
                if not (output / name).is_file()
                or (output / name).read_bytes() != value.encode("utf-8")
            ]
            print(json_text({"checked_files": len(files), "mismatches": mismatches}), end="")
            return 1 if mismatches else 0
        if output.exists() and any(output.iterdir()):
            marker = output / "package-metadata.json"
            previous = json.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else {}
            if not args.replace_generated or previous.get("generated_by") != GENERATOR_ID:
                raise ValueError(
                    "Refusing to overwrite existing data; only an explicitly selected generated package can be replaced"
                )
            if previous.get("revision") == args.revision and any(
                not (output / name).is_file()
                or (output / name).read_bytes() != value.encode("utf-8")
                for name, value in files.items()
            ):
                raise ValueError("Changed generated content requires a new revision")
        for relative, value in files.items():
            path = output / relative
            if path.is_symlink() or any(
                parent.is_symlink() for parent in path.parents if parent.is_relative_to(output)
            ):
                raise ValueError("Refusing to write through symbolic links")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value.encode("utf-8"))
        print(
            json_text(
                {"written_files": len(files), "output": str(output), "revision": args.revision}
            ),
            end="",
        )
        return 0
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
