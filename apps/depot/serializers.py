from rest_framework import serializers


class DriverSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    employee_id = serializers.CharField()


class BusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    model = serializers.CharField()
    plate_number = serializers.CharField()
    color = serializers.CharField()
    capacity = serializers.IntegerField()
    status = serializers.CharField()
    fuel = serializers.CharField()
    driver = DriverSerializer()


class RouteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class ScheduleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    day_of_week = serializers.CharField()
    direction = serializers.CharField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    route = RouteSerializer()
    bus = BusSerializer()


class StationSerializer(serializers.Serializer):
    city = serializers.CharField()
    address = serializers.CharField(required=False, allow_null=True)
    street = serializers.CharField(required=False, allow_null=True)


class TripSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    trip_nr = serializers.CharField()
    date = serializers.DateField()
    status = serializers.CharField()
    price = serializers.FloatField()
    departure_time = serializers.TimeField(required=False, allow_null=True)
    arrival_time = serializers.TimeField(required=False, allow_null=True)
    from_station = StationSerializer()
    to_station = StationSerializer()
    schedule = ScheduleSerializer()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        from_station = data.get("from_station", {})
        to_station = data.get("to_station", {})

        bus = data.get("schedule", {}).get("bus", {})
        driver = bus.get("driver", {})
        route = data.get("schedule", {}).get("route", {})

        return {
            "id": data.get("id"),
            "trip_nr": data.get("trip_nr"),
            "date": data.get("date"),
            "status": data.get("status"),
            "price": data.get("price"),
            "origin": from_station.get("city", ""),
            "destination": to_station.get("city", ""),
            "start_time": data.get("departure_time"),
            "end_time": data.get("arrival_time"),
            "bus_capacity": bus.get("capacity", 0),
            "bus_model": bus.get("model", ""),
            "bus_plate_number": bus.get("plate_number", ""),
            "driver_name": driver.get("name", ""),
            "driver_phone": driver.get("phone_number", ""),
            "route_name": route.get("name", ""),
        }


class TripDetailSerializer(serializers.Serializer):
    trip_info = TripSerializer()
    seats = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dictionary of seat numbers to status, e.g. {'1': 'available', '2': 'reserved'}",
    )
