from __future__ import annotations

from django.test import TestCase

from tests.models import BoxJoinModel, JoinItemForeignKey


class JoinManagerTest(TestCase):
    def setUp(self) -> None:
        for i in range(20):
            BoxJoinModel.objects.create(name=f'name_{i}')

        JoinItemForeignKey.objects.create(
            weight=10, belonging=BoxJoinModel.objects.get(name='name_1')
        )
        JoinItemForeignKey.objects.create(weight=20)

    def test_self_join(self) -> None:
        a_slice = BoxJoinModel.objects.all()[0:10]
        with self.assertNumQueries(1):
            result = a_slice.join()
        self.assertEqual(result.count(), 10)

    def test_self_join_with_where_statement(self) -> None:
        qs = BoxJoinModel.objects.filter(name='name_1')
        result = qs.join()
        self.assertEqual(result.count(), 1)

    def test_join_with_other_qs(self) -> None:
        item_qs = JoinItemForeignKey.objects.filter(weight=10)
        boxes = BoxJoinModel.objects.all().join(qs=item_qs)
        self.assertEqual(boxes.count(), 1)
        self.assertEqual(boxes[0].name, 'name_1')

    def test_reverse_join(self) -> None:
        box_qs = BoxJoinModel.objects.filter(name='name_1')
        items = JoinItemForeignKey.objects.all().join(box_qs)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items[0].weight, 10)
