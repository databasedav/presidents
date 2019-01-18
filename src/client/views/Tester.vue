<template>
    <div>
        <TestPlayer :namespace='"adsaijflasjdf"'></TestPlayer>
        <TestPlayer :namespace='"bsadfasdfasdf"'></TestPlayer>
        <TestPlayer :namespace='"cdfsasdfasdf"'></TestPlayer>
        <TestPlayer :namespace='"ddgsadfhadfg"'></TestPlayer>
    </div>
</template>

<script>
import TestPlayer from '../components/TestPlayer.vue'

export default {
    name: 'Tester',
    components: {
        TestPlayer
    }
}
</script>

<style>

</style>
