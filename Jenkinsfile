node ("docker") {
    VERSION_STRING="$MAJOR_VERSION.$MINOR_VERSION.$BUILD_NUMBER"
    def image = null
    stage("Git Pull") {
        // Get from github
        git credentialsId: 'github_pk', url: "git@github.com:martinnj/distrowatch-dumper.git", branch: 'main'
    }
    stage("Configure") {
        sh "sed -i 's/###VERSION###/$VERSION_STRING/g' setup.py"
        sh "sed -i 's/###VERSION###/$VERSION_STRING/g' dumper.py"
        sh "sed -i 's/###VERSION###/$VERSION_STRING/g' Dockerfile"
    }
    stage("Build Docker Image") {
        // When using the extra arguments, we need to apply the final arguments
        // oursleves as well. Hence the " ." at the end.
        image = docker.build("distrowatch-dumper:$VERSION_STRING", "--no-cache -f Dockerfile .")
    }
    stage("Push") {
        docker.withRegistry("$REGISTRY_URL") {
            image.push()
            image.push("latest")
        }
    }
    stage("Tag") {
        sshagent(['github_pk']) {
            sh "git tag -a v$VERSION_STRING -m \"Tagged by $BUILD_URL\""
            sh "git push --tags"
        }
    }
    stage("Clean") {
        cleanWs()
    }
}
