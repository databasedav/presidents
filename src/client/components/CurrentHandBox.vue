<template>
  <div>
    <span>{{ current_hand_str }}</span>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'CurrentHandBox',
  computed: {
    ...mapGetters(['current_hand_str'])
  }
}
</script>
<style>

</style>
