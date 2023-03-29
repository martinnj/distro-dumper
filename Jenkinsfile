node ("python3") {
    VERSION_STRING="$MAJOR_VERSION.$MINOR_VERSION.$BUILD_NUMBER"
    def image = null
    stage("Git Pull") {
        // Get from github
        git credentialsId: "github_pk", url: "git@github.com:martinnj/distro-dumper.git", branch: "main"
    }
    stage("Configure") {
        // Set version in relevant files.
        sh "sed -i 's/###VERSION###/$VERSION_STRING/g' setup.py"
        sh "sed -i 's/###VERSION###/$VERSION_STRING/g' dumper.py"
        sh "sed -i 's/###VERSION###/$VERSION_STRING/g' Dockerfile"

        // Create dir to pick up analysis reports.
        sh "mkdir reports"
    }
    stage("Static Analysis") {
        withPythonEnv("/home/jenkins/.pyenv/shims/python3.9") {
            sh "python --version"
            sh "pip --version"
            sh "pip install -r requirements-dev.txt"
            sh "tox -e lint > reports/pylint.log || true"
            // TODO: sh "tox -e typecheck"

            // Publish pylint results.
            def checkstyle = scanForIssues(
                blameDisabled: true,
                forensicsDisabled: true,
                sourceDirectory: ".",
                tool: pyLint(pattern: "reports/pylint.log")
            )
            publishIssues issues: [checkstyle]
        }
    }
    stage("Testing") {
        // TODO: This is really ugly. >_< I would love for "withPythonEnv" to discover pyenv itself.
        parallel py39: {
            withPythonEnv("/home/jenkins/.pyenv/shims/python3.9") {
                sh "python --version && pip --version"
                sh "pip install --upgrade pip \"tox<4.0.0\""
                sh "tox -e cov"
                // Publist test & coverage reports.
                junit("reports/xunit.xml")
                cobertura coberturaReportFile: "reports/cov.xml"
            }
        }, py310: {
            withPythonEnv("/home/jenkins/.pyenv/shims/python3.10") {
                sh "python --version && pip --version"
                sh "pip install --upgrade pip \"tox<4.0.0\""
                sh "tox -e py310"
            }
        }, py311: {
            withPythonEnv("/home/jenkins/.pyenv/shims/python3.11") {
                sh "python --version && pip --version"
                sh "pip install --upgrade pip \"tox<4.0.0\""
                sh "tox -e py311"
            }
        }
    }
    stage("Stash") {
        // Stash the files we need to build the Docker image.
        stash(
            name: "docker-application",
            includes: ".dockerignore, Dockerfile, dumper.py, requirements.txt, distrodumper/**",
            excludes: "__pycache__"
        )
    }
}
node("docker") {
    stage("Unstash") {
        // Unstash the Docker image requisites.
        unstash(name: "docker-application")
    }
    stage("Build Docker Image") {
        // When using the extra arguments, we need to apply the final arguments
        // oursleves as well. Hence the " ." at the end.
        image = docker.build("distro-dumper:$VERSION_STRING", "--no-cache -f Dockerfile .")
    }
    stage("Push") {
        docker.withRegistry("$REGISTRY_URL") {
            image.push()
            image.push("latest")
        }
    }
    stage("Tag") {
        sshagent(["github_pk"]) {
            sh "git tag -a v$VERSION_STRING -m \"Tagged by $BUILD_URL\""
            sh "git push --tags"
        }
    }
    stage("Clean") {
        cleanWs()
    }
}
