<template>
  <div>
    <v-btn
      v-if='!play_unlocked'
      @click="$emit('unlock')"
      color='error'
    >
      unlock
    </v-btn>

    <v-btn
      v-else
      @click="$emit('lock')"
      color='error'
    >
      lock
    </v-btn>

    <v-btn
      color='info'
    >
      store hand
    </v-btn>

    <v-btn
      @click="$emit('pass')"
      color='warning'
    >
      pass
    </v-btn>

    <v-btn
      v-if='play_unlocked'
      @click="$emit('play')"
      color='success'
    >
      play
    </v-btn>

    <v-btn
      v-else
      :disabled='true'
      color='success'
    >
      play
    </v-btn>

    <br>
    <button @click="$emit('restart')">restart</button>
  </div>
</template>

<script>
import io from 'socket.io-client'

import { namespaced_getter } from '../utils/utils'

export default {
  name: 'ButtonBox',
  props: {
    namespace: String
  },

  computed: {
    play_unlocked () {
      return namespaced_getter(this.namespace, 'play_unlocked')
    },
    
  },
}
</script>
