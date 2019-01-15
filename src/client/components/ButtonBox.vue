<template>
  <v-container grid-list-md>
    <v-layout>
      <v-flex xs12>
        <AskingOptions
          v-if='trading && asker'
          :namespace='this.namespace'
          @asking_click='$emit("asking_click", $event)'
        >
        </AskingOptions>
      </v-flex>
    </v-layout>
      
    <v-layout row wrap justify-space-around height='100%'>
      <!-- lock/unlock button -->
      <v-flex xs5>
        <v-btn
          @click="$emit(lock_unlock_str)"
          block
          color='error'
        >
          {{ lock_unlock_str }}
          <v-icon v-if='!unlocked' small right>fa-lock</v-icon>
          <v-icon v-else small right>fa-unlock</v-icon>
        </v-btn>
      </v-flex>

      <v-flex xs5>
        <v-btn
          v-if='trading && asker'
          @click="$emit(alt_play_button_str)"
          block
          :disabled='!unlocked'
          color='success'
        >
          {{ alt_play_button_str }}
          <v-icon v-if='alt_play_button_str === "ask"' small right>fa-question</v-icon>
          <v-icon v-else-if='alt_play_button_str === "give"' small right>fa-gift</v-icon>
          <template v-else>
            <v-icon small right>fa-question</v-icon><v-icon small right>fa-gift</v-icon>
          </template>
        </v-btn>

        <v-btn
          v-else-if='trading && giver'
          @click='$emit("give")'
          block
          :disabled='!unlocked'
          color='success'
        >
          give
        </v-btn>

        <v-btn
          v-else
          @click="$emit('play')"
          block
          :disabled='!unlocked'
          color='success'
        >
          play
          <v-icon right>play_arrow</v-icon>
        </v-btn>
      </v-flex>
    </v-layout>

    <v-layout row wrap justify-space-around>

      <v-flex xs5>
         <v-btn
          color='info'
          block
          :disabled='true'
        >
          store hand
        </v-btn>
      </v-flex>

      <v-flex xs5>
        <v-btn
          @click='$emit("pass")'
          block
          color='warning'
        >
          pass
          <v-icon right>skip_next</v-icon>
        </v-btn>
      </v-flex>

      
    </v-layout>
  </v-container>
</template>

<script>
import io from 'socket.io-client'
import AskingOptions from './AskingOptions.vue'

import { namespaced_getter } from '../utils/utils'

export default {
  name: 'ButtonBox',

  props: {
    namespace: String
  },

  components: {
    AskingOptions
  },

  computed: {
    unlocked () {
      return this.$store.state[this.namespace].unlocked
    },

    lock_unlock_str () {
      return this.unlocked ? 'lock' : 'unlock'
    },

    pass_unlocked () {
      return this.$store.state[this.namespace].pass_unlocked
    },

    asker () {
      return this.$store.state[this.namespace].asker
    },

    giver () {
      return this.$store.state[this.namespace].giver
    },

    trading () {
      return this.$store.state[this.namespace].trading
    },

    alt_play_button_str () {
      return this.$store.getters[`${this.namespace}/alt_play_button_str`]
    }
  }
}
</script>

<style scoped>
.v-btn {
  height: 60px;
  text-transform: lowercase !important;
}
</style>
