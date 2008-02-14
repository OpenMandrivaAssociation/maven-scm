# Copyright (c) 2000-2005, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

%define _with_gcj_support 1
%define gcj_support %{?_with_gcj_support:1}%{!?_with_gcj_support:%{?_without_gcj_support:0}%{!?_without_gcj_support:%{?_gcj_support:%{_gcj_support}}%{!?_gcj_support:0}}}

%define maven_settings_file %{_builddir}/%{name}/settings.xml
%define namedversion 1.0-beta-3

Name:           maven-scm
Version:        1.0
Release:        %mkrel 0.1.b3.2.1.3
Epoch:          0
Summary:        Common API for doing SCM operations
License:        Apache Software License
Group:          Development/Java
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:            http://maven.apache.org/scm

Source0:        %{name}-%{version}-beta-3.tar.gz
# svn export 
#   http://svn.apache.org/repos/asf/maven/scm/tags/maven-scm-1.0-beta-3/
#   maven-scm/
# tar czf maven-scm-1.0-beta-3.tar.gz maven-scm/
Source1:        %{name}-jpp-depmap.xml
Source2:        %{name}-mapdeps.xsl
Source3:        %{name}-add-plexusutils-dep.xml


%if ! %{gcj_support}
BuildArch:      noarch
%endif
BuildRequires:  java-rpmbuild >= 0:1.6
BuildRequires:  maven2 >= 2.0.4-6
BuildRequires:  maven2-plugin-compiler
BuildRequires:  maven2-plugin-install
BuildRequires:  maven2-plugin-jar
BuildRequires:  maven2-plugin-javadoc
BuildRequires:  maven2-plugin-plugin
BuildRequires:  maven2-plugin-release
BuildRequires:  maven2-plugin-resources
BuildRequires:  maven2-plugin-surefire
BuildRequires:  maven2-common-poms >= 1.0-3
BuildRequires:  modello >= 1.0-0.a8
BuildRequires:  modello-maven-plugin >= 1.0-0.a8
BuildRequires:  plexus-utils >= 1.2
BuildRequires:  saxon-scripts

Requires:       junit >= 3.8.2
Requires:       jakarta-commons-collections >= 3.1
Requires:       modello >= 1.0-0.a8
Requires:       modello-maven-plugin >= 1.0-0.a8
Requires:       oro >= 2.0.8
Requires:       plexus-utils >= 1.2
Requires:       velocity >= 1.4

%if %{gcj_support}
BuildRequires:          java-gcj-compat-devel
%endif

Requires(post):    jpackage-utils >= 0:1.7.2
Requires(postun):  jpackage-utils >= 0:1.7.2

%description
Maven SCM supports Maven 2.x plugins (e.g. maven-release-plugin) and other
tools (e.g. Continum) in providing them a common API for doing SCM operations.

%package test
Summary:        Tests for %{name}
Group:          Development/Java
Requires:       maven-scm = %{epoch}:%{version}-%{release}

%if %{gcj_support}
BuildRequires:          java-gcj-compat-devel
%endif

%description test
Tests for %{name}.

%package javadoc
Summary:        Javadoc for %{name}
Group:          Development/Java
Requires(pre):  /bin/rm,/bin/ls
Requires(post): /bin/rm

%description javadoc
Javadoc for %{name}.

%prep
%setup -q -n %{name}

#FIXME: Bazaar tests fail since the executable is no available. Disable 
#       the tests.
rm -rf maven-scm-providers/maven-scm-provider-bazaar/src/test

%build

(cd maven-scm-api
cp -p pom.xml pom.xml.noplexusutils.xml
saxon -o pom.xml pom.xml.noplexusutils.xml %{SOURCE2} map=%{SOURCE3}
)

export MAVEN_REPO_LOCAL=$(pwd)/.m2/repository
mkdir -p $MAVEN_REPO_LOCAL

mvn-jpp \
        -e \
        -Dmaven.repo.local=$MAVEN_REPO_LOCAL \
        -Dmaven.test.failure.ignore=true \
        install javadoc:javadoc

%install
rm -rf $RPM_BUILD_ROOT
# jars/poms
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}/%{name}
install -d -m 755 $RPM_BUILD_ROOT/%{_datadir}/maven2/poms

# remove test files, they are used for build time testing
#find  -type f -name "*cvstest*" -exec rm -f '{}' \; \
#-o -type f -name "*svntest*" -exec rm -f '{}' \;

for jar in `find . -type f -name "*.jar" | grep -E "target/.*.jar$"`; do
        newname=`basename $jar | sed -e s:^maven-scm-::g`
        install -pm 644 $jar \
          $RPM_BUILD_ROOT%{_javadir}/%{name}/$newname
done

(cd $RPM_BUILD_ROOT%{_javadir}/%{name} && for jar in *-%{namedversion}*; \
  do ln -sf ${jar} `echo $jar| sed  "s|-%{namedversion}||g"`; done)

#poms (exclude the svn/cvstest poms. They are unnecessary)
# ignore 
#  1) poms in target/ (they are either copies, or temps)
#  2) poms in src/test/ (they are poms needed for tests only)
for i in `find . -name pom.xml | grep -v \\\./pom.xml | \
   grep -v target | grep -v src/test`; do
        artifactname=`basename \`dirname $i\``
        jarname=`echo $artifactname | sed -e s:^maven-scm-::g`
        cp -p $i $RPM_BUILD_ROOT%{_datadir}/maven2/poms/JPP.$artifactname.pom
        %add_to_maven_depmap org.apache.maven.scm $artifactname %{namedversion} JPP/%{name} $jarname
done
cp -p pom.xml $RPM_BUILD_ROOT%{_datadir}/maven2/poms/JPP.maven-scm-scm.pom
%add_to_maven_depmap org.apache.maven.scm maven-scm %{namedversion} JPP/maven-scm scm

# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}

for docsdir in `find -name apidocs`; do
        subdir=`echo $docsdir | \
          awk -F / '{print $(NF-3)}' | sed -e s:^maven-scm-::g`
        install -dm 755 \
          $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}/$subdir
        cp -pr $docsdir/* \
          $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}/$subdir
done

ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name}

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
%if %{gcj_support}
%{update_gcjdb}
%endif
%update_maven_depmap

%postun
%if %{gcj_support}
%{clean_gcjdb}
%endif
%update_maven_depmap

%if %{gcj_support}
%post test
%{update_gcjdb}
%endif

%if %{gcj_support}
%postun test
%{clean_gcjdb}
%endif

%files
%defattr(-,root,root,-)
%dir %{_javadir}
%dir %{_javadir}/%{name}
%{_datadir}/maven2
%{_javadir}/%{name}/api*
%{_javadir}/%{name}/client*
%{_javadir}/%{name}/manager-plexus*
%{_javadir}/%{name}/plugin*
%{_javadir}/%{name}/provider-bazaar*
%{_javadir}/%{name}/provider-clearcase*
%{_javadir}/%{name}/provider-local*
%{_javadir}/%{name}/provider-perforce*
%{_javadir}/%{name}/provider-cvs-commons*
%{_javadir}/%{name}/provider-cvsexe*
%{_javadir}/%{name}/provider-svn-commons*
%{_javadir}/%{name}/provider-svnexe*
%{_javadir}/%{name}/provider-starteam*
%{_javadir}/%{name}/provider-vss*
%config(noreplace) %{_mavendepmapfragdir}/*
%doc LICENSE.txt NOTICE.txt

%if %{gcj_support}
%dir %attr(-,root,root) %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/api-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/client-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/manager-plexus-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/plugin-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-bazaar-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-clearcase-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-cvs-commons-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-cvsexe-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-local-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-perforce-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-starteam-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-svn-commons-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-svnexe-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-vss-1.0-beta-3.jar.*
%endif

%files test
%defattr(-,root,root,-)
%{_javadir}/%{name}/provider-cvstest*
%{_javadir}/%{name}/provider-svntest*
%{_javadir}/%{name}/test*

%if %{gcj_support}
%dir %attr(-,root,root) %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-cvstest-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/test-1.0-beta-3.jar.*
%attr(-,root,root) %{_libdir}/gcj/%{name}/provider-svntest-1.0-beta-3.jar.*
%endif

%files javadoc
%defattr(-,root,root,-)
%{_javadocdir}/*
