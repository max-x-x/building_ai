def extract_object_info(object_data):
    """
    Безопасно извлекает информацию об объекте из API ответа.
    Возвращает структурированные данные даже при отсутствии полей.
    """
    try:
        # Проверяем на Forbidden
        if isinstance(object_data, dict) and object_data.get("detail") == "Forbidden":
            raise Exception("Что вы не относитесь к этому объекту")
        
        # Проверяем на другие ошибки API
        if isinstance(object_data, dict) and "error" in object_data:
            raise Exception(f"Ошибка API: {object_data['error']}")
        # Основная информация об объекте
        result = {
            "Название объекта": object_data.get("name", "Не указано"),
            "Адрес": object_data.get("address", "Не указано"),
            "Статус объекта": object_data.get("status", "Не указано"),
            "Можно ли продолжать работы": object_data.get("can_proceed", False),
            "Прогресс выполнения (%)": object_data.get("work_progress", 0),
            "Дата создания": object_data.get("created_at", "Не указано"),
            "Участники": {},
            "Области": [],
            "Поставки": [],
            "Планы работ": [],
            "Статистика": {}
        }
        
        # Участники проекта
        participants = {}
        
        # ССК
        ssk = object_data.get("ssk", {})
        participants["ССК"] = {
            "ФИО": ssk.get("full_name", "Не указано"),
            "Почта": ssk.get("email", "Не указано")
        }
        
        # Прораб
        foreman = object_data.get("foreman", {})
        participants["ПРОРАБ"] = {
            "ФИО": foreman.get("full_name", "Не указано"),
            "Почта": foreman.get("email", "Не указано")
        }
        
        # ИКО
        iko = object_data.get("iko", {})
        participants["ИКО"] = {
            "ФИО": iko.get("full_name", "Не указано"),
            "Почта": iko.get("email", "Не указано")
        }
        
        result["Участники"] = participants
        
        # Области
        areas = object_data.get("areas", [])
        for area in areas:
            area_info = {
                "name": area.get("name", "Не указано")
            }
            result["Области"].append(area_info)
        
        # Поставки
        deliveries = object_data.get("deliveries", [])
        for delivery in deliveries:
            work_item = delivery.get("work_item", {})
            delivery_info = {
                "name": work_item.get("name", "Не указано") if work_item else "Не указано",
                "planned_date": delivery.get("planned_date", "Не указано")
            }
            result["Поставки"].append(delivery_info)
        
        # Планы работ
        work_plans = object_data.get("work_plans", [])
        for plan in work_plans:
            work_items = plan.get("work_items", [])
            for item in work_items:
                work_item_info = {
                    "name": item.get("name", "Не указано"),
                    "status": item.get("status", "Не указано")
                }
                result["Планы работ"].append(work_item_info)
        
        # Статистика
        result["Статистика"] = {
            "deliveries_count": object_data.get("deliveries_count", 0),
            "work_plans_count": object_data.get("work_plans_count", 0),
            "prescriptions_count": object_data.get("prescriptions_count", 0),
            "open_prescriptions_count": object_data.get("open_prescriptions_count", 0),
            "works_count": object_data.get("works_count", 0),
            "daily_checklists_count": object_data.get("daily_checklists_count", 0)
        }
        
        return result
        
    except Exception as e:
        # В случае любой ошибки возвращаем базовую структуру
        return {
            "Название объекта": "Ошибка извлечения",
            "Адрес": "Ошибка извлечения",
            "Статус объекта": "Ошибка извлечения",
            "Можно ли продолжать работы": False,
            "Прогресс выполнения (%)": 0,
            "Дата создания": "Ошибка извлечения",
            "Участники": {
                "ССК": {"ФИО": "Ошибка", "Почта": "Ошибка"},
                "ПРОРАБ": {"ФИО": "Ошибка", "Почта": "Ошибка"},
                "ИКО": {"ФИО": "Ошибка", "Почта": "Ошибка"}
            },
            "Области": [],
            "Поставки": [],
            "Планы работ": [],
            "Статистика": {
                "deliveries_count": 0,
                "work_plans_count": 0,
                "prescriptions_count": 0,
                "open_prescriptions_count": 0,
                "works_count": 0,
                "daily_checklists_count": 0
            },
            "Ошибка": str(e)
        }
