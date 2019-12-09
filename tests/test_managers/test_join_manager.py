from django.test import TestCase

from tests.models import JoinItemForeignKey, BoxJoinModel


class JoinManagerTest(TestCase):
    def setUp(self):
        for i in range(20):
            BoxJoinModel.objects.create(name='name_{i}'.format(i=i))

        JoinItemForeignKey.objects.create(
            weight=10, belonging=BoxJoinModel.objects.get(name='name_1')
        )
        JoinItemForeignKey.objects.create(weight=20)

    def test_self_join(self):
        a_slice = BoxJoinModel.objects.all()[0:10]
        with self.assertNumQueries(1):
            result = a_slice.join()
        self.assertEquals(result.count(), 10)

    def test_self_join_with_where_statement(self):
        qs = BoxJoinModel.objects.filter(name='name_1')
        result = qs.join()
        self.assertEquals(result.count(), 1)

    def test_join_with_other_qs(self):
        item_qs = JoinItemForeignKey.objects.filter(weight=10)
        boxes = BoxJoinModel.objects.all().join(qs=item_qs)
        self.assertEquals(boxes.count(), 1)
        self.assertEquals(boxes[0].name, 'name_1')

    def test_reverse_join(self):
        box_qs = BoxJoinModel.objects.filter(name='name_1')
        items = JoinItemForeignKey.objects.all().join(box_qs)
        self.assertEquals(items.count(), 1)
        self.assertEquals(items[0].weight, 10)
