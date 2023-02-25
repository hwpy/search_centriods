import json
from math import radians
from typing import Any, Dict, List, Union
import requests

from sklearn.metrics.pairwise import haversine_distances

class DistancesFinder():
    """Класс содержит функции для поиска суммарного расстояния между наборами координат. \n
    Для расчета расстояния по автодорогам используется метод get_shortest_dist_by_car(coord_list: List[List[Union[int, float]]]) \n
        Требуется передавать списки в формате [[lon, lat], [lon, lat], ...].
    Для расчета расстояния для авиатранспорта по прямой (с учетом траектории вдоль земного шара) \n
        используется метод get_shortest_dist_by_car(coord_list: List[List[Union[int, float]]]). \n
        Требуется передавать списки в формате [[lon, lat], [lon, lat], ...]
    """
    def __init__(
        self
    ):
        pass


    def _validate_coord_value(self, coords: List[Union[float, int]]):
        """Проверка на диапазон широты и долготы
        Широта в диапазоне [-180, 180]
        Долгота в диапазоне [-90, 90]

        Аргументы:
            - coords (List[float]) - Координаты [долгота, широта]
        """
        lon, lat  = coords
        assert -180 <= lon <= 180, f"Некорректное значение долготы {lon}!"
        assert -90 <= lat <= 90, f"Некорректное значение широты {lat}!"


    def _check_coords(self, coord_list: List[List[Union[float, int]]]) -> List[List[Union[float, int]]]:
        """Проверка что набор координат соответствует виду List[List[Union[float, int]]]

        Аргументы:
            - coord_list (List[List[Union[float, int]]]) - Список координат точек посещения

        Возвращает:
            List[List[Union[float, int]]] - - Провалидированный список координат точек посещения

        Исключения:
            - ValueError: "Некорректное значение {coord_list}. Список коорданат для расчета расстояния должен состоять минимум из двух пунктов"
            - ValueError: "Некорректный тип {type(coords)}! Входное значение должно быть List[List],\n
                где каждый внутренний спислок состоит из 2-х элементов (int | float)"
            - ValueError: "Некорректный размер списка: {len(coords)}. Координаты должны содержать 2 элемента, долготу и широту"
            - ValueError: "Некорректный тип {type(coord)}! Долгота и широта должны иметь тип int | float."
        """
        if len(coord_list) < 2:
            raise ValueError(f"Некорректное значение {coord_list}. Список коорданат для расчета расстояния должен состоять минимум из двух пунктов")
        for coords in coord_list:
            if not isinstance(coords, (list, set, tuple)):
                raise ValueError(f"Некорректный тип {type(coords)}! Входное значение должно быть List[List],\
                    где каждый внутренний спислок состоит из 2-х элементов (int | float)")
            else:
                if len(coords) != 2:
                    raise ValueError(f"Некорректный размер списка: {len(coords)}. Координаты должны содержать 2 элемента, долготу и широту")
                for coord in coords:
                    if not isinstance(coord, (float, int)):
                        raise ValueError(f"Некорректный тип {type(coord)}! Долгота и широта должны иметь тип int | float.")
                self._validate_coord_value(coords=coords)
        return coord_list

    def _create_url_for_req(self, coord_list: List[List[Union[int, float]]]) -> str:
        """Собрать url к API OSRM для получения ответа с маршрутом и расстоянием

        Аргументы:
            - coord_list (List[List[Union[int, float]]]) - [[lon, lat], [lon, lat], ...]

        Возвращает:
            str - url
        """
        coords_str = ";".join(str(f"{coord[1]},{coord[0]}") for coord in [coords for coords in coord_list])
        return f"http://router.project-osrm.org/route/v1/car/{coords_str}?overview=false"

    def _get_routes_by_car(self, coord_list):
        url = self._create_url_for_req(coord_list)
        req = requests.get(url)
        routes = json.loads(req.content)
        return routes

    def _get_shortest_route_dist(self, routes: Dict[Any, Any]):
        sum_dist = 0
        for route in routes.get("routes"):
            sum_dist += route.get('distance')
        return sum_dist

    def get_shortest_dist_by_car(self, coord_list: List[List[Union[int, float]]]):
        """
        coord_list[[lon, lat], [lon, lat], ...]
        """
        try:
            coord_list = self._check_coords(coord_list)
            routes = self._get_routes_by_car(coord_list)
            dist = self._get_shortest_route_dist(routes)
            dist_km = dist/1000
        except Exception:
            dist_km = self.get_haversine_dist(coord_list)
        return dist_km

    def _calc_haversine_distance_2p(self, coord_pair):
        point_from = coord_pair[0]
        point_to = coord_pair[1]
        point_from_in_radians = [radians(_) for _ in point_from]
        point_to_in_radians = [radians(_) for _ in point_to]
        result = haversine_distances([point_from_in_radians, point_to_in_radians])
        dist_km = result * 6371000/1000  # Радиус Земли
        return dist_km[0][1]

    def _pairwise(self, list_of_points):
        return zip(list_of_points, list_of_points[1:])

    def get_haversine_dist(self, coord_list: List[List[Union[int, float]]]):
        """
        coord_list[[lon, lat], [lon, lat], ...]
        """
        coord_list = self._check_coords(coord_list)
        sum_dist_km = 0
        for point_a, point_b in self._pairwise(coord_list):
            point_from = [point_a[1], point_a[0]]
            point_to = [point_b[1], point_b[0]]
            sum_dist_km += self._calc_haversine_distance_2p([point_from, point_to])
        return sum_dist_km