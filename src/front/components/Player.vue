<template>
  <v-container>
    
    <v-layout column>
      <v-flex xs12>
        <OtherPlayerBox
          :namespace='this.rnsp'
        >
        </OtherPlayerBox>
      </v-flex>
      
      <v-flex xs12>
        <AlertSnackbar
          :namespace='this.rnsp'
        >
        </AlertSnackbar>
      </v-flex>
      
      <v-flex xs12>
        <InPlayBox
          :namespace='this.rnsp'
        >
        </InPlayBox>
      </v-flex>
      
      <v-flex xs12>
        <MessageBox
          :namespace='this.rnsp'
        >
        </MessageBox>
      </v-flex>

      <v-layout justify-center>
        <v-flex xs8>
          <PlayerStrip
            :namespace='this.rnsp'
            :spot='this.spot'
          >
          </PlayerStrip>
        </v-flex>
      </v-layout>

      <CardBox
        :namespace='this.rnsp'
        @card_click='this.card_click'
      >
      </CardBox>

      <v-flex xs12>
        <ButtonBox
          :namespace='this.rnsp'
          @unlock='this.unlock'
          @lock='this.lock'
          @play='this.play'
          @unlock_pass='this.unlock_pass'
          @pass='this.pass'
          @ask='this.ask'
          @give='this.give'
          @asking_click='this.asking_click'
        >
        </ButtonBox>
      </v-flex>
    </v-layout>
    
  </v-container>
</template>

<script>
import CardBox from './CardBox.vue'
import ButtonBox from './ButtonBox.vue'
import InPlayBox from './InPlayBox.vue'
import AlertSnackbar from './AlertSnackbar.vue'
import MessageBox from './MessageBox.vue'
import PlayerStrip from './PlayerStrip.vue'
import OtherPlayerBox from './OtherPlayerBox.vue'

export default {
  name: 'Player',
  
  components: {
    CardBox,
    ButtonBox,
    InPlayBox,
    AlertSnackbar,
    MessageBox,
    PlayerStrip,
    OtherPlayerBox
  },

  props: {
    rnsp: String
  },

  methods: {
    card_click(card) {
      this.$store.dispatch(`${this.rnsp}/emit_card_click`, {
        'card': card
      })
    },

    unlock () {
      this.$store.dispatch(`${this.rnsp}/emit_unlock`)
    },

    lock () {
      this.$store.dispatch(`${this.rnsp}/emit_lock`)
    },

    play () {
      this.$store.dispatch(`${this.rnsp}/emit_play`)
    },

    unlock_pass () {
      this.$store.dispatch(`${this.rnsp}/emit_unlock_pass`)
    },

    pass () {
      this.$store.dispatch(`${this.rnsp}/emit_pass`)
    },

    ask () {
      this.$store.dispatch(`${this.rnsp}/emit_ask`)
    },

    give () {
      this.$store.dispatch(`${this.rnsp}/emit_give`)
    },

    asking_click (value) {
      this.$store.dispatch(`${this.rnsp}/emit_asking_click`, {
        'value': value
      })
    }
  },

  computed: {
    on_turn () {
      return this.$store.state[this.rnsp].on_turn
    },

    spot () {
      return this.$store.state[this.rnsp].spot
    }
  },
}
</script>

<style>

</style>
