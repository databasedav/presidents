<template>
  <div>
<<<<<<< HEAD
    <!-- <span>{{  }}</span> -->
=======
    <span>{{ current_hand_str }}</span>
>>>>>>> 862b65305567d81fa5982ca1bcdd8b9d67c091c0
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
