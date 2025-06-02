from typing import Type, Dict, Any, Callable, TypeVar


class ServiceManager:
    "Service Manager to register services"

    _services: Dict[str, Any] = {}

    @classmethod
    def register_service(cls, service_name: str, service_instance: Any) -> None:
        "Register services in _services"
        cls._services[service_name] = service_instance

    @classmethod
    def get(cls, name: str) -> Any:
        return cls._services.get(name)

    @classmethod
    def register(cls, name: str) -> Callable:
        def wrapper(service_class: Any) -> Any:
            instance = service_class
            cls.register_service(name, instance)
            return instance

        return wrapper
