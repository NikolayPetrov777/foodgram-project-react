from rest_framework import mixins, viewsets


class ListRetriveViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет только для list, retrieve."""

    pass


class ListViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет только для list."""

    pass
