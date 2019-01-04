<template>
    <div>
        <TestPlayer :namespace='"a"'></TestPlayer>
        <TestPlayer :namespace='"b"'></TestPlayer>
        <TestPlayer :namespace='"c"'></TestPlayer>
        <TestPlayer :namespace='"d"'></TestPlayer>
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
