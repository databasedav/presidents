<template>
  <div>
    <span>{{ current_hand_desc }}</span><br><br>
    <Card
      v-for='card in cards'
      :key='card.id'
      :card='card.value'
      :is_selected='card.is_selected'
      :functional='true'
    ></Card>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Card from './Card.vue'

export default {
  name: 'CardBox',
  components: {
    Card
  },
  computed: {
    ...mapGetters(['cards', 'current_hand_desc'])
  },
}
</script>
